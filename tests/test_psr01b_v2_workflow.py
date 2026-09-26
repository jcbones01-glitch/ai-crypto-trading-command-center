"""Real subprocess CLI/claim/post-claim regressions, synthetic GitHub only."""
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/psr01b-development-execution-v1.yml'

# Test-only transport adapter loaded BEFORE production imports. It never stubs
# authority, reservation, identity, runtime, CLI, or claim verification logic.
TRANSPORT = r'''
import json, os, pathlib, urllib.request
from urllib.error import HTTPError
state_path = pathlib.Path(os.environ['FAKE_GITHUB_STATE'])
class Response:
    def __init__(self, data): self.data = data
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self): return json.dumps(self.data).encode()
def fake(request, *args, **kwargs):
    url = request.full_url
    if not url.startswith('https://api.github.com/repos/synthetic/repo/git/'):
        raise AssertionError('non-GitHub/source network access: ' + url)
    state = json.loads(state_path.read_text())
    if request.get_method() == 'GET':
        if '/git/ref/' in url:
            ref = 'refs/' + url.split('/git/ref/')[1]
            if ref not in state['refs']: raise HTTPError(url,404,'absent',{},None)
            return Response({'ref':ref,'object':{'sha':state['refs'][ref]}})
        return Response(state['tags'][url.rsplit('/',1)[1]])
    value = json.loads(request.data)
    if url.endswith('/git/tags'):
        sha = 'c' * 40
        result = {'sha':sha,'tag':value['tag'],'message':value['message'],
                  'object':{'sha':value['object'],'type':value['type']}}
        state['tags'][sha] = result
    elif url.endswith('/git/refs'):
        if value['ref'] in state['refs']: raise HTTPError(url,422,'exists',{},None)
        state['refs'][value['ref']] = value['sha']
        result = {'ref':value['ref'],'object':{'sha':value['sha']}}
    else: raise AssertionError(url)
    state_path.write_text(json.dumps(state))
    return Response(result)
urllib.request.urlopen = fake
if os.environ.get('FORBID_DOWNLOADER') == '1':
    import sys
    class BlockDownloader:
        def find_spec(self, fullname, path=None, target=None):
            if fullname == 'research_core.data_ingestion':
                raise AssertionError('rehearsal imported downloader module')
    sys.meta_path.insert(0, BlockDownloader())
'''


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root, text=True).strip()


@pytest.fixture
def sequence(tmp_path):
    root = tmp_path / 'checkout'
    root.mkdir()
    for name in ('src', 'research/governance', 'research/scripts'):
        shutil.copytree(ROOT / name, root / name, ignore=shutil.ignore_patterns('__pycache__'))
    workflow = root / '.github/workflows'
    workflow.mkdir(parents=True)
    for file in (ROOT / '.github/workflows').glob('*.yml'):
        shutil.copy2(file, workflow / file.name)
    # The real frozen inventory includes test blobs; copy tests as metadata only.
    shutil.copytree(ROOT / 'tests', root / 'tests', ignore=shutil.ignore_patterns('__pycache__'))
    git(root, 'init', '-q')
    git(root, 'config', 'user.name', 'Synthetic Test')
    git(root, 'config', 'user.email', 'synthetic@example.invalid')
    git(root, 'add', '.')
    git(root, 'commit', '-qm', 'synthetic candidate')
    candidate = git(root, 'rev-parse', 'HEAD')
    path = root / 'research/governance/psr01b_implementation_freeze_v1.json'
    freeze = json.loads(path.read_text())
    freeze['implementation'].update(implementation_candidate_commit=candidate,
        reviewed_implementation_commit=candidate, independent_implementation_reviewed=True)
    freeze['implementation_file_git_blob_sha1'] = {
        n:git(root,'hash-object',n) for n in freeze['implementation_file_git_blob_sha1']}
    f = freeze['future_governance']
    f.update(execution_authorized=True, reviewed_candidate_anchor_created=True)
    f['execution_scope']['implementation_candidate_commit'] = candidate
    f['execution_scope']['one_shot_claim_ref'] = 'refs/tags/psr01b-development-one-shot-claim-v2'
    for name in freeze['protected_access']:
        freeze['protected_access'][name] = name.startswith('empirical_')
    freeze['review_anchor_ref'] = 'refs/heads/psr-01b-bounded-implementation-reviewed-v4'
    freeze['review_anchor_sha'] = candidate
    path.write_text(json.dumps(freeze, indent=2)+'\n')
    git(root, 'add', str(path))
    git(root, 'commit', '-qm', 'synthetic authorization')
    head = git(root, 'rev-parse', 'HEAD')
    transport = tmp_path / 'transport'
    transport.mkdir()
    (transport / 'sitecustomize.py').write_text(TRANSPORT)
    state = tmp_path / 'github.json'
    state.write_text(json.dumps({'refs':{freeze['review_anchor_ref']:candidate},'tags':{}}))
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(transport),str(root/'src'),str(root)]),
        FAKE_GITHUB_STATE=str(state), GITHUB_REPOSITORY='synthetic/repo', GITHUB_SHA=head,
        GITHUB_TOKEN='synthetic-no-network', GITHUB_RUN_ID='12345', GITHUB_RUN_ATTEMPT='1',
        GITHUB_ACTOR='synthetic-actor', GITHUB_EVENT_NAME='workflow_dispatch',
        GITHUB_OUTPUT=str(tmp_path/'outputs'), PSR01B_EXECUTION_MODE='execute',
        PSR01B_DEVELOPMENT_V1_CONFIRMATION=f'PSR01B_DEVELOPMENT_V1:{candidate}:{head}',
        OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1')
    env.pop('FORBID_DOWNLOADER',None)
    return root, env, state, candidate


def invoke(root, env, command):
    result = subprocess.run(command, cwd=root, env=env, text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


def workflow_commands(root, env, *, relative=False):
    steps = yaml.safe_load(WORKFLOW.read_text())['jobs']['execute']['steps']
    commands = [s['run'] for s in steps if s.get('name') in (
        'Reserve result path and verify authority before claim',
        'Atomically create durable PSR-01B one-shot claim')]
    assert len(commands) == 2
    assert all('--result-path' not in c for c in commands)
    for command in commands:
        if relative:
            command = command.rstrip() + ' --result-path research/experiments/psr01b_development_v2/result.json\n'
        invoke(root, env, ['bash','-eu','-c',command])
    for line in Path(env['GITHUB_OUTPUT']).read_text().splitlines():
        key,value=line.split('=',1)
        env['PSR01B_DEVELOPMENT_V1_'+key.upper()]=value


@pytest.mark.parametrize('relative',[False,True])
def test_real_workflow_cli_claim_then_absolute_presource_verification(sequence, relative):
    root, env, state, candidate = sequence
    workflow_commands(root, env, relative=relative)
    invoke(root, env, [sys.executable,'-c', '''
from research_core.psr01b_runner import load_implementation_freeze, verify_frozen_execution_identity
from research_core.psr01b_execution_lock import DEFAULT_RESULT_PATH, assert_execution_environment
f=load_implementation_freeze()
p=verify_frozen_execution_identity(runner_label="ubuntu-24.04")
assert_execution_environment(p["implementation_candidate_commit"],f,DEFAULT_RESULT_PATH)
print("REAL_SEQUENCE_PRE_SOURCE_PASS")
'''])
    record=json.loads((root/'research/experiments/psr01b_development_v2/result.json.reservation').read_text())
    assert record['result_path']==str(root/'research/experiments/psr01b_development_v2/result.json')
    assert not (root/'research/experiments/psr01b_development_v2/result.json').exists()


def test_rehearsal_full_sequence_never_imports_or_calls_downloader(sequence):
    root, env, state, candidate = sequence
    env.update(PSR01B_EXECUTION_MODE='rehearsal', FORBID_DOWNLOADER='1',
        PSR01B_DEVELOPMENT_V1_CONFIRMATION=f'PSR01B_REHEARSAL_V2:{candidate}:{env["GITHUB_SHA"]}')
    workflow_commands(root,env)
    out=invoke(root,env,[sys.executable,'research/scripts/run_psr01b_development_v1.py'])
    assert 'PSR01B_REHEARSAL_V2_PRE_SOURCE_PASS' in out
    refs=json.loads(state.read_text())['refs']
    assert 'refs/tags/psr01b-rehearsal-12345-1' in refs
    assert 'refs/tags/psr01b-development-one-shot-claim-v2' not in refs
    assert not (root/'research/experiments/psr01b_development_v2').exists()
    # Rehearsal cannot be redirected onto the real claim through forwarded env.
    env['PSR01B_DEVELOPMENT_V1_CLAIM_REF']='refs/tags/psr01b-development-one-shot-claim-v2'
    bad=subprocess.run([sys.executable,'research/scripts/run_psr01b_development_v1.py'],cwd=root,env=env,capture_output=True,text=True)
    assert bad.returncode != 0
    assert 'claim ref is missing or incorrect' in bad.stderr


def test_original_candidate_reservation_mismatch_reproduces(tmp_path, monkeypatch):
    # Execute the two actual function definitions from the reviewed old blob,
    # not a hand-written approximation of the bug. CI fetches full history.
    source=subprocess.check_output(['git','show','9ef234210163dba8633a11acc74be0de8581be7c:src/research_core/psr01b_execution_lock.py'],cwd=ROOT,text=True)
    assert hashlib.sha1(b'blob '+str(len(source.encode())).encode()+b'\0'+source.encode()).hexdigest()=='02ca038b18db105670f93650246f3cafdf800bd3'
    nodes=[n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name in {'reservation_path','reserve_result_path','assert_result_reservation'}]
    from research_core.psr01b_core import PSR01BError
    scope={'Path':Path,'os':os,'json':json,'PSR01BError':PSR01BError}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'<reviewed-9ef2342-reservation>','exec'),scope)
    monkeypatch.chdir(tmp_path)
    scope['reserve_result_path'](Path('result.json'),candidate='a'*40,executing_sha='b'*40)
    with pytest.raises(PSR01BError,match='result reservation identity mismatch'):
        scope['assert_result_reservation'](tmp_path/'result.json',candidate='a'*40,executing_sha='b'*40)
    print('OLD_9EF2342_RELATIVE_ABSOLUTE_MISMATCH_REPRODUCED')


@pytest.mark.parametrize('failure',['unauthorized','confirmation','real_result_path'])
def test_rehearsal_fails_closed_before_claim(sequence, failure):
    root, env, state, candidate = sequence
    env.update(PSR01B_EXECUTION_MODE='rehearsal', FORBID_DOWNLOADER='1',
        PSR01B_DEVELOPMENT_V1_CONFIRMATION=f'PSR01B_REHEARSAL_V2:{candidate}:{env["GITHUB_SHA"]}')
    args=[sys.executable,'-m','research_core.psr01b_execution_lock','preflight',
          '--repository',env['GITHUB_REPOSITORY'],'--sha',env['GITHUB_SHA']]
    if failure == 'unauthorized':
        path=root/'research/governance/psr01b_implementation_freeze_v1.json'
        freeze=json.loads(path.read_text())
        freeze['future_governance']['execution_authorized']=False
        path.write_text(json.dumps(freeze))
        expected='execution authorization is not approved'
    elif failure == 'confirmation':
        env['PSR01B_DEVELOPMENT_V1_CONFIRMATION']='wrong'
        expected='exact PSR-01B manual confirmation string required'
    else:
        args += ['--result-path','research/experiments/psr01b_development_v2/result.json']
        expected='rehearsal result path mismatch'
    result=subprocess.run(args,cwd=root,env=env,capture_output=True,text=True)
    assert result.returncode != 0 and expected in result.stderr
    assert len(json.loads(state.read_text())['refs']) == 1  # synthetic review anchor only
    assert not (root/'research/experiments/psr01b_development_v2').exists()
