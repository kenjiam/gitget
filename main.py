import os

import argparse
import requests
import toml

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGES_TOML = os.path.join(BASE_DIR, "packages.toml")

def get_latest_release_data(target):
    url = f"https://api.github.com/repos/{target}/releases/latest"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return None
    return response.json()

def get_latest_version(data):
    version_latest = data.get("tag_name")
    return version_latest

def get_assets(data):
    assets_raw = data.get("assets", [])
    assets = []
    for row in assets_raw:
        asset = row.get("browser_download_url")
        assets.append(asset)
    return assets

def download_file(url):
    filename = url.split("/")[-1]
    print(f"\nDownloading {filename}...")
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Finished downloading {filename}.")

    else:
        print("Failed to download the file.")

def install(target):
    def choose_asset(assets):
        if not assets:
            print("There is no binary asset.")
            return

        print("Choose from the following URLs:")
        for idx, url in enumerate(assets, start=1):
            print(f"{idx}. {url}")

        while True:
            try:
                choice = int(input("\nInput the number of the URL you want to install: "))
                if 1 <= choice <= len(assets):
                    break
                else:
                    print(f"\nInvalid input. Please enter a number between 1 and {len(assets)}.")
            except ValueError:
                print(f"\nInvalid input. Please enter a number between 1 and {len(assets)}.")
        return choice
    def update_packages_toml(target, version):
        author = target.split("/")[0]
        repo_name = target.split("/")[1]

        if os.path.exists(PACKAGES_TOML):
            try:
                with open(PACKAGES_TOML, "r", encoding="utf-8") as f:
                    data = toml.load(f)
            except Exception as e:
                print(f"Error reading {PACKAGES_TOML}: {e}")
                data = {}
        else:
            data = {}

        new_entry = {"owner": author, "version": version}
        data[repo_name] = new_entry

        sorted_data = {k: data[k] for k in sorted(data, key=lambda k: k.lower())}

        try:
            with open(PACKAGES_TOML, "w", encoding="utf-8") as f:
                toml.dump(sorted_data, f)
        except Exception as e:
            print(f"Error writing to {PACKAGES_TOML}: {e}")

    data = get_latest_release_data(target)
    if data is None:
        print("There are no releases.")
        return

    version_latest = get_latest_version(data)
    print(f"latest tag: {version_latest}\n")

    assets = get_assets(data)
    choice = choose_asset(assets)
    if choice is None:
        return
    selected_url = assets[choice - 1]

    download_file(selected_url)
    update_packages_toml(target, version_latest)

def list():
    try:
        with open(PACKAGES_TOML, "r", encoding="utf-8") as f:
            packages = toml.load(f)
    except Exception as e:
        print(f"Error reading {PACKAGES_TOML}: {e}")
        return

    header = f"{'Name':<40} {'Author':<30} {'Version':<15} {'Available':<15}"
    separator = "-" * len(header)
    print(header)
    print(separator)

    for key, value in packages.items():
        repo_name = key.split("/")[-1]
        author = value.get("author", "")
        version = value.get("version", "")
        data = get_latest_release_data(f"{author}/{repo_name}")
        version_latest = get_latest_version(data)
        if version != version_latest:
            print(f"{repo_name:<40} {author:<30} {version:<15} {version_latest:<15}")
        else:
            print(f"{repo_name:<40} {author:<30} {version:<15} {'':<15}")

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", title="commands")

    # install
    install_parser = subparsers.add_parser("install", help="install")
    install_parser.add_argument("target", help="target")

    # list
    list_parser = subparsers.add_parser("list", help="list")
    list_parser.add_argument("target", nargs="?", help="target")

    # search
    search_parser = subparsers.add_parser("search", help="search")
    search_parser.add_argument("target", help="target")

    args = parser.parse_args()
    target = args.target

    if args.command == "install":
        install(target)
        return
    elif args.command == "list":
        list()

if __name__ == "__main__":
    main()
