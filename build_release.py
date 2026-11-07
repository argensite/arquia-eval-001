"""Build a byte-reproducible source ZIP from an explicit inventory; no network."""
import argparse
import json
from pathlib import Path
import sys
import zipfile
from measurement import canonical,file_hash,git_state,sha
from verify_package import safe_file

ROOT=Path(__file__).resolve().parent


def inventory(root=ROOT):
    names=json.loads((root/'PACKAGE_FILES.json').read_text(encoding='utf-8'))
    if not isinstance(names,list) or not all(isinstance(x,str) for x in names) or len(names)!=len(set(names)):
        raise ValueError('invalid package inventory')
    if 'PACKAGE_FILES.json' not in names or 'CHECKSUMS.sha256' in names:
        raise ValueError('inventory must include itself and exclude generated checksums')
    return names


def manifest(files):
    return ''.join(sha(data)+'  '+name+'\n' for name,data in sorted(files.items())).encode('utf-8')


def write_manifest(root=ROOT):
    files={n:safe_file(root,n).read_bytes() for n in inventory(root)}
    (root/'CHECKSUMS.sha256').write_bytes(manifest(files))


def build(output,root=ROOT):
    files={n:safe_file(root,n).read_bytes() for n in inventory(root)}
    # Archive identity is explicitly a declaration carried by the source package.
    source=git_state() if root==ROOT else {'commit':None,'dirty':None,'status':[]}
    files['SOURCE_IDENTITY.json']=canonical(source)+b'\n'
    files['PACKAGE_FILES.json']=(json.dumps(sorted(set(files)|{'PACKAGE_FILES.json'}),indent=2)+'\n').encode()
    files['CHECKSUMS.sha256']=manifest(files)
    version=(root/'VERSION').read_text().strip();prefix='ARQUIA-EVAL-001-v'+version+'/'
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    archive=output/('ARQUIA-EVAL-001-v'+version+'.zip')
    # ZIP_STORED avoids compressor/version differences across OS/runtime builds.
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_STORED) as z:
        for name,data in sorted(files.items()):
            info=zipfile.ZipInfo(prefix+name,(2026,11,7,0,0,0));info.create_system=3
            info.external_attr=0o100644<<16;info.compress_type=zipfile.ZIP_STORED
            z.writestr(info,data)
    digest=file_hash(archive)
    archive.with_suffix('.zip.sha256').write_text(digest+'  '+archive.name+'\n',encoding='utf-8')
    return {'archive':str(archive),'sha256':digest,'files':len(files),'source':source,
            'scope':'source archive only; historical results unchanged; no execution attribution'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'dist')
    p.add_argument('--write-manifest',action='store_true');a=p.parse_args()
    if a.write_manifest:write_manifest();return 0
    print(json.dumps(build(a.output),indent=2));return 0
if __name__=='__main__':sys.exit(main())
