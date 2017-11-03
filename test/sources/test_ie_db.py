''' test ie_db (import/export folders/images to/from the database) '''

import os
import pytest

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

from db import *
session = open_mem_db()

from ie_db import *
from test_ie_fs import test_scan_dir_set_expected_list
from test_ie_fs import test_scan_dir_sel_selected_list, test_scan_dir_sel_expected_list
from test_ie_fs import test_scan_file_set_corbett_psds_expected_list
from test_ie_fs import test_scan_file_sel_corbett_psds_selected_list
from test_ie_fs import test_scan_file_sel_corbett_psds_expected_list

base_path = '\\users\\user\\PycharmProjects\\im\\test\\import-export sources'
# TODO: get PyCharm/pytest to provide this, up to the last directory

def check_worklist_no_fs_folders(
        session, fs_source, source_type, paths, expected_list):
    worklist = get_ie_worklist(
        session, fs_source, source_type, paths)

    if len(worklist) != len(expected_list):
        pass
    assert len(worklist) == len(expected_list)
    for work, expected in zip(worklist, expected_list):
        assert work.fs_folder is None
        assert work.ie_folder.fs_name == expected[0]

def check_worklist_with_fs_folders(
        session, fs_source, source_type, paths, expected_list):
    fs_folders = []
    for expected in expected_list:
        fs_folder = FsFolder.add(session, fs_source, expected[0])
        fs_folders.append(fs_folder)
    worklist = get_ie_worklist(
        session, fs_source, source_type, paths)
    assert len(worklist) == len(expected_list)
    for work, expected, fs_folder in zip(
            worklist, expected_list, fs_folders):
        assert work.fs_folder is fs_folder
        assert work.ie_folder.fs_name == expected[0]
        session.expunge(fs_folder)

def test_get_workist_dir_set_my_dirs():
    path = os.path.join(base_path, 'my format')
    fs_source = FsSource.add(
        session, 'c:', path, FsSourceType.DIR, readonly=True, tag_source=None)
    check_worklist_no_fs_folders(
        session, fs_source, SourceType.DIR_SET, [path],
        test_scan_dir_set_expected_list
    )
    check_worklist_with_fs_folders(
        session, fs_source, SourceType.DIR_SET, [path],
        test_scan_dir_set_expected_list
    )
    session.commit()

def test_get_workist_dir_sel_my_dirs():
    path = os.path.join(base_path, 'my format')
    fs_source = FsSource.add(
        session, 'c:', path, FsSourceType.DIR, readonly=True, tag_source=None)
    check_worklist_no_fs_folders(
        session, fs_source, SourceType.DIR_SEL, test_scan_dir_sel_selected_list,
        test_scan_dir_sel_expected_list
    )
    fs_folders = []
    check_worklist_with_fs_folders(
        session, fs_source, SourceType.DIR_SEL,
        test_scan_dir_sel_selected_list,
        test_scan_dir_sel_expected_list
    )
    session.commit()

def test_get_worklist_file_set_corbett_psds():
    path = os.path.join(base_path, 'main1415 corbett psds')
    fs_source = FsSource.add(
        session, 'c:', path, FsSourceType.FILE, readonly=True, tag_source=None)
    check_worklist_no_fs_folders(
        session, fs_source, SourceType.FILE_SET, [path],
        test_scan_file_set_corbett_psds_expected_list
    )
    check_worklist_with_fs_folders(
        session, fs_source, SourceType.FILE_SET, [path],
        test_scan_file_set_corbett_psds_expected_list
    )
    session.commit()

def test_get_worklist_file_sel_corbett_psds():
    path = os.path.join(base_path, 'main1415 corbett psds')
    fs_source = FsSource.add(
        session, 'c:', path, FsSourceType.FILE, readonly=True, tag_source=None)
    check_worklist_no_fs_folders(
        session, fs_source, SourceType.FILE_SEL,
        test_scan_file_sel_corbett_psds_selected_list,
        test_scan_file_sel_corbett_psds_expected_list
    )
    check_worklist_with_fs_folders(
        session, fs_source, SourceType.FILE_SEL,
        test_scan_file_sel_corbett_psds_selected_list,
        test_scan_file_sel_corbett_psds_expected_list
    )
    session.commit()
