"""Small reversible patch to the actual SGLang unquantized linear path.

Uses env A8_GEMM_ENABLE=1 and PYTHONPATH=/path/to/a8_gemm_opt.
Never changes semantics when switch is off. Only patch after microbench wins.
"""
import argparse
from pathlib import Path

START = 'class UnquantizedLinearMethod(LinearMethodBase):'
END = 'class UnquantizedFusedMoEMethod('
LINE = '        return F.linear(x, layer.weight, bias)'
INJECTION = '''        # A8_BEGIN: opt-in GEMM experiment. Disabled by default.
        import os as _a8_os
        if _a8_os.environ.get("A8_GEMM_ENABLE") == "1":
            from a8_kernel import try_fast_linear as _a8_linear
            return _a8_linear(x, layer.weight, bias)
        # A8_END
        return F.linear(x, layer.weight, bias)'''


def main():
    p = argparse.ArgumentParser()
    p.add_argument('source', help='Path to sglang/srt/layers/quantization/unquant.py')
    p.add_argument('mode', choices=('install', 'restore'))
    args = p.parse_args()
    src = Path(args.source)
    backup = src.with_name(src.name + '.a8_original')
    if args.mode == 'restore':
        if not backup.exists():
            raise SystemExit('No backup. Refusing restoration guess.')
        if src.exists() and 'A8_BEGIN' not in src.read_text():
            raise SystemExit('Current file has no A8 patch; refusing to overwrite.')
        src.write_bytes(backup.read_bytes())
        backup.unlink()
        print('RESTORED:', src)
        return
    data = src.read_text()
    if 'A8_BEGIN' in data:
        print('Already patched:', src)
        return
    if backup.exists():
        raise SystemExit('Existing backup; aborting to protect it.')
    if START not in data or END not in data:
        raise SystemExit('Unexpected SGLang version: class anchors not found')
    a, rest = data.split(START, 1)
    section, end = rest.split(END, 1)
    if section.count(LINE) != 1:
        raise SystemExit(f'Expected 1 F.linear call in UnquantizedLinearMethod, got {section.count(LINE)}')
    patched = a + START + section.replace(LINE, INJECTION) + END + end
    compile(patched, str(src), 'exec')
    backup.write_bytes(src.read_bytes())
    try:
        src.write_text(patched)
    except BaseException:
        src.write_bytes(backup.read_bytes())
        raise
    print('PATCHED:', src)
    print('Original backup:', backup)
    print('Disabled by default. Enable per server with A8_GEMM_ENABLE=1 and PYTHONPATH=...')


if __name__ == '__main__':
    main()
