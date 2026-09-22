"""共有スキルの登録・検証を一時ディレクトリで確認する。"""

import contextlib
import io
import os
from pathlib import Path
import runpy
import tempfile
import unittest


register = runpy.run_path(str(Path(__file__).parents[1] / 'scripts/register-skills.py'))['register']


class RegisterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / '.llm-agents/skills'
        self.source.mkdir(parents=True)

    def skill(self, name='example', content=None):
        path = self.source / name
        path.mkdir()
        (path / 'SKILL.md').write_text(content if content is not None else
                                     f'---\nname: {name}\ndescription: 検証用\n---\n本文\n', encoding='utf-8')
        return path

    def run_register(self, check=False):
        with contextlib.redirect_stdout(io.StringIO()):
            register(self.root, check=check)

    def test_registration_is_repeatable(self):
        skill = self.skill()
        self.run_register()
        self.run_register()
        self.run_register(check=True)
        for folder in ('.agents/skills', '.claude/skills'):
            link = self.root / folder / 'example'
            self.assertTrue(link.is_symlink())
            self.assertEqual(link.resolve(), skill)
            self.assertFalse(os.path.isabs(os.readlink(link)))

    def test_check_does_not_create_directories(self):
        self.skill()
        with self.assertRaises(ValueError):
            self.run_register(check=True)
        self.assertFalse((self.root / '.agents').exists())
        self.assertFalse((self.root / '.claude').exists())

    def test_conflict_preserves_files_and_prevents_partial_registration(self):
        self.skill('aaa')
        self.skill('zzz')
        conflict = self.root / '.agents/skills/zzz'
        conflict.parent.mkdir(parents=True)
        conflict.write_text('保存する', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.run_register()
        self.assertEqual(conflict.read_text(encoding='utf-8'), '保存する')
        self.assertFalse((conflict.parent / 'aaa').exists())
        self.assertFalse((self.root / '.claude').exists())

    def test_missing_skill_or_document_is_detected_without_deletion(self):
        for remove_directory in (False, True):
            with self.subTest(remove_directory=remove_directory):
                skill = self.skill()
                self.run_register()
                (skill / 'SKILL.md').unlink()
                if remove_directory:
                    skill.rmdir()
                for check in (False, True):
                    with self.assertRaisesRegex(ValueError, '本体または SKILL.md'):
                        self.run_register(check=check)
                for folder in ('.agents/skills', '.claude/skills'):
                    link = self.root / folder / 'example'
                    self.assertTrue(link.is_symlink())
                    link.unlink()
                if not remove_directory:
                    skill.rmdir()

    def test_invalid_metadata_prevents_registration(self):
        cases = [
            ('a' * 64, None),
            ('Bad_Name', None),
            ('example', '# frontmatter なし'),
            ('example', '---\nname: different\ndescription: 説明\n---'),
            ('example', '---\nname: example\ndescription: " "\n---'),
            ('example', '---\nname: example\n---'),
            ('example', '---\nname: example\ndescription: 123\n---'),
            ('example', '---\nname: [\n---'),
            ('example', '---\n- example\n---'),
        ]
        for name, content in cases:
            with self.subTest(name=name, content=content):
                skill = self.skill(name, content)
                with self.assertRaises(ValueError):
                    self.run_register()
                self.assertFalse((self.root / '.agents').exists())
                (skill / 'SKILL.md').unlink()
                skill.rmdir()

    def test_multiline_yaml_and_maximum_name(self):
        name = 'a' * 63
        self.skill(name, f'---\nname: "{name}"\ndescription: >\n  複数行の\n  説明\n---\n本文')
        self.run_register()
        self.run_register(check=True)

    def test_directory_without_document_warns_and_is_skipped(self):
        (self.source / 'broken').mkdir()
        (self.source / '.gitkeep').write_text('', encoding='utf-8')
        self.skill()
        errors = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(errors):
            register(self.root)
        self.assertIn('broken', errors.getvalue())
        self.assertNotIn('.gitkeep', errors.getvalue())
        for folder in ('.agents/skills', '.claude/skills'):
            self.assertFalse((self.root / folder / 'broken').exists())
            self.assertTrue((self.root / folder / 'example').is_symlink())

    def test_unrelated_links_are_preserved(self):
        parent = self.root / '.agents/skills'
        parent.mkdir(parents=True)
        link = parent / 'other'
        link.symlink_to('../../external', target_is_directory=True)
        self.run_register(check=True)
        self.assertTrue(link.is_symlink())

    def test_parent_symlink_is_rejected_even_without_skills(self):
        destination = self.root / 'external'
        destination.mkdir()
        (self.root / '.agents').symlink_to(destination, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.run_register(check=True)
        self.assertEqual(list(destination.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
