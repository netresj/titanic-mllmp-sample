#!/usr/bin/env python3
"""共有スキルへの参照を各エージェントの探索場所に登録する。"""

import argparse
import os
from pathlib import Path
import re
import sys


def validate_skill(skill):
    """共有スキルの命名規則と必須メタデータを検証する。"""
    import yaml

    if len(skill.name) >= 64 or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', skill.name):
        raise ValueError(f'スキル名が不正です（64文字未満の小文字英数字とハイフン）: {skill.name}')
    lines = (skill / 'SKILL.md').read_text(encoding='utf-8').splitlines()
    if not lines or lines[0] != '---' or '---' not in lines[1:]:
        raise ValueError(f'frontmatter がありません: {skill}')
    end = lines.index('---', 1)
    try:
        metadata = yaml.safe_load('\n'.join(lines[1:end]))
    except yaml.YAMLError as error:
        raise ValueError(f'frontmatter の YAML が不正です: {skill}: {error}') from error
    if not isinstance(metadata, dict):
        raise ValueError(f'frontmatter はマッピングが必要です: {skill}')
    if metadata.get('name') != skill.name:
        raise ValueError(f'name とディレクトリ名が一致しません: {skill}')
    description = metadata.get('description')
    if not isinstance(description, str) or not description.strip():
        raise ValueError(f'description は空でない文字列が必要です: {skill}')


def register(root, check=False):
    root = Path(root).resolve()
    source = root / '.llm-agents/skills'
    if not source.is_dir():
        raise ValueError(f'共有スキルの配置先がありません: {source}')
    # 登録元が空でも、残ったリンクと登録先の衝突を検出する。
    parents = [root / folder for folder in ('.claude/skills', '.agents/skills')]
    for parent in parents:
        for ancestor in (parent.parent, parent):
            if ancestor.is_symlink() or (ancestor.exists() and not ancestor.is_dir()):
                raise ValueError(f'登録先には通常のディレクトリが必要です: {ancestor}')
        if parent.is_dir():
            for link in sorted(parent.iterdir()):
                if not link.is_symlink():
                    continue
                target_path = Path(os.path.abspath(link.parent / os.readlink(link)))
                if source in target_path.parents and not (link / 'SKILL.md').is_file():
                    raise ValueError(f'共有スキルの本体または SKILL.md がありません: {link}')
    pending = []
    for skill in sorted(source.iterdir()):
        if not (skill / 'SKILL.md').is_file():
            # 作成途中のディレクトリを見落とさないよう、無言では飛ばさない。
            if skill.is_dir():
                print(f'警告: SKILL.md がないため登録しません: {skill.relative_to(root)}', file=sys.stderr)
            continue
        validate_skill(skill)
        # Copilot も .claude/skills を探索するため、専用のコピーは作らない。
        for parent in parents:
            link = parent / skill.name
            target = os.path.relpath(skill, parent)
            if link.is_symlink() and os.path.normcase(os.path.normpath(os.readlink(link))) == os.path.normcase(os.path.normpath(target)):
                continue
            if os.path.lexists(link):
                raise ValueError(f'既存の登録先は上書きしません: {link}')
            pending.append((link, target))
    if check and pending:
        raise ValueError('未登録のスキルがあります: ' + ', '.join(str(p) for p, _ in pending))
    # 衝突を全件確認してから作成する。既存のファイルやリンクは削除しない。
    for link, target in pending:
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(target, target_is_directory=True)
        print(f'登録: {link.relative_to(root)} -> {target}')
    print('共有スキルの登録を確認しました。')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='変更せず登録状態を確認する')
    args = parser.parse_args()
    try:
        register(Path(__file__).resolve().parents[2], args.check)
    except ModuleNotFoundError as error:
        if error.name != 'yaml':
            raise
        print('エラー: PyYAML が必要です。.llm-agents/README.md の依存の導入手順を確認してください。', file=sys.stderr)
        return 1
    except (OSError, ValueError) as error:
        print(f'エラー: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
