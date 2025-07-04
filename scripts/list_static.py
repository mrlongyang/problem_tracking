from django.contrib.staticfiles.finders import get_finders

def run():
    print("Static files found by Django:")
    for finder in get_finders():
        for path, storage in finder.list([]):
            print(f"{path} -> {storage.path(path)}")