from app.core.manager import CodeGraphManager

def test_project_contains(create_project):
    project = create_project
    
    src_folder = project.add_folder(folder_name="src", folder_path=project.path+"/src")
    src_folder.add_file(file_name="main.py", file_path=project.path+ "/main.py")

    
    assert len(project.get_files()) == 0
    assert len(project.get_folders()) == 1

    

    
    