from io import StringIO
from unittest import TestCase
from unittest.mock import patch
from yapf_diff.lib import parseUDiff
from yapf_diff import cli, getDiff, main


class TestCli(TestCase):

  def test_all(self):
    defaults = {'diff': False, 'in_place': False, 'from_git_diff': True}
    params = {
        ('--from-git-diff',): {
            **defaults
        },
        ('--from-git-diff', 'HEAD~3'): {
            **defaults, 'from_git_diff': 'HEAD~3'
        },
        # TODO: if this tool ever does NOT come from a diff, revise the below.
        ('--from-git-diff', '0'): {
            **defaults, 'from_git_diff': '0'
        },
        ('--from-git-diff', 'False'): {
            **defaults, 'from_git_diff': 'False'
        },
        ('--from-git-diff', 'false'): {
            **defaults, 'from_git_diff': 'false'
        },
    }

    for argv, expected in params.items():
      with self.subTest(argv=argv):
        self.assertEqual({**cli.parse_args(argv).__dict__}, expected)


# common fixtures
normal_git_diff = '''diff --git a/bar.py b/bar.py
index ca88001..df9c674 100644
--- a/bar.py
+++ b/bar.py
@@ -1,5 +1,6 @@
 def spam():
   # spam
+  # eggs
   return 'spam'


@@ -8,4 +9,4 @@ def wonderful():

   return 'spam'  # spam
                  # spam
-                 # spam
+                 # eggs
diff --git a/foo.py b/foo.py
index 2ac86a8..663719d 100644
--- a/foo.py
+++ b/foo.py
@@ -1,3 +1,2 @@
 def spam():
-
   pass
'''


class TestDiffParsing(TestCase):

  def test_git_diff(self):
    self.assertEqual(
        parseUDiff(normal_git_diff), {
            './foo.py': [(1, 3)],
            './bar.py': [(1, 7), (9, 13)],
        })


class TestGetDiff(TestCase):

  @patch('sys.stdin', new_callable=lambda: StringIO(normal_git_diff))
  def test_raw_diff_input(self, mock_stdin):
    result = getDiff(True)  # use stdin
    self.assertEqual(result, mock_stdin)

  @patch('yapf_diff.run', return_value=normal_git_diff)
  def test_get_diff(self, mock_run):
    getDiff()
    mock_run.assert_called_with(['git', 'diff'])

  @patch('yapf_diff.run', return_value=normal_git_diff)
  def test_get_diff_from_base(self, mock_run):
    getDiff('HEAD~3')
    mock_run.assert_called_with(['git', 'diff', 'HEAD~3'])


class TestMain(TestCase):

  @patch('os.chdir')
  @patch('yapf_diff.run', return_value='/path/to/git/dir')
  @patch('sys.stdin', new_callable=lambda: normal_git_diff)
  @patch('yapf_diff.FormatFile')
  def test_pre_commit(self, mock_formatter, mock_stdin, mock_run, mock_chdir):
    print(mock_formatter)
    main([])  # should use `git diff`
    mock_chdir.assert_called_with('/path/to/git/dir')
    mock_formatter.assert_any_call(
        '/path/to/git/dir/foo.py',
        in_place=False,
        lines=[(1, 3)],
        print_diff=False,
    )
    mock_formatter.assert_any_call(
        '/path/to/git/dir/bar.py',
        lines=[(1, 7), (9, 13)],
        print_diff=False,
        in_place=False)
