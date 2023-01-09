import configparser
import os
import sys
import traceback
from glob import fnmatch, glob
from sys import exit

import boto3

client = boto3.client('s3')
paginator = client.get_paginator('list_objects')
print('new version')

def human_size(num, suffix="B"):
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, "Yi", suffix)


def get_dir(bucket_name, prefix):
    assert len(prefix) == 0 or prefix.endswith('/')
    l = []
    for result in paginator.paginate(Bucket=bucket_name, Prefix=prefix, Delimiter='/'):
        if result.get('CommonPrefixes') is not None:
            l.extend([subdir.get('Prefix')[len(prefix):] for subdir in result.get('CommonPrefixes')])
        if result.get('Contents') is not None:
            l.extend([obj.get('Key')[len(prefix):] for obj in result.get('Contents') if obj['Size'] > 0])
    return l


def is_dir(bucket_name, prefix):
    assert len(prefix) == 0 or prefix.endswith('/')
    for result in paginator.paginate(Bucket=bucket_name, Prefix=prefix, Delimiter='/'):
        if result.get('CommonPrefixes') is not None:
            return True
        if result.get('Contents') is not None:
            return True
    return False


def print_folder(bucket, current_path, limit=20):
    list_dir = get_dir(bucket.name, current_path)
    print()
    if len(list_dir) == 0:
        print("  (directory is empty)")
    else:
        print("(" + str(len(list_dir)) + " items)")
        for k, item in enumerate(list_dir):
            if k == limit:
                print("  ...")
                print("  (command 'l' to see the full list)")
                break
            if item.endswith("/"):
                print(
                    f'  {ConsoleColors.BOLD}{item:30}{ConsoleColors.END_COLOR} {"<dir>":>10}'
                )
            else:
                print(
                    f"  {ConsoleColors.BOLD}{item:30}{ConsoleColors.END_COLOR} {human_size(bucket.Object(current_path + item).content_length):>10}\t{str(bucket.Object(current_path + item).last_modified):} "
                )
    print()
    return list_dir


class ConsoleColors:
    if os.name != "nt":
        HEADER = "\033[95m"
        OK_BLUE = "\033[94m"
        OK_GREEN = "\033[92m"
        WARNING = "\033[93m"
        FAIL = "\033[91m"
        END_COLOR = "\033[0m"
        BOLD = "\033[1m"
        UNDERLINE = "\033[4m"
    else:
        HEADER = OK_BLUE = OK_GREEN = WARNING = FAIL = END_COLOR = BOLD = UNDERLINE = ""


def main():
    print("\nS3 Browser - github.com/replon/s3b")
    print("============================================")
    boto_session = None

    try:
        if len(sys.argv) >= 2:
            try:
                boto_session = boto3.Session(profile_name=sys.argv[1])
            except Exception:
                # botocore.exceptions.ProfileNotFound
                print(
                    ConsoleColors.FAIL,
                    "[FAIL] Cannot found AWS credential profile '" + sys.argv[1] + "'",
                )
                print("  \nUsage: s3b [profile_name]\n")
                exit()
        else:
            boto_session = boto3.Session()
            if boto_session.get_credentials() is None:
                print(ConsoleColors.FAIL, "[FAIL] Cannot found default AWS access key.")
                print("  \nUsage: s3b [profile_name]\n")
                print(
                    "  \nCreate a file '~/.aws/credentials' and store your key like this.."
                )
                print(
                    "\n[default]\naws_access_key_id = your_access_key_id\naws_secret_access_key = "
                    "your_secret_access_key\n "
                )
                exit()

        print("Connecting to S3 using...")
        print("  profile_name:", boto_session.profile_name)
        print("  aws_access_key_id:", boto_session.get_credentials().access_key)
        print("  aws_secret_access_key:", boto_session.get_credentials().secret_key)

        s3 = None
        bucket_names = []
        try:
            s3 = boto_session.resource("s3")
            bucket_names = [bucket.name for bucket in s3.buckets.all()]
        except Exception:
            print(ConsoleColors.FAIL, "[FAIL] Unable to connect to S3 \nbye :(")
            exit()

        bucket_select = ""
        while not bucket_select.isnumeric() or int(bucket_select) not in range(
            len(bucket_names)
        ):
            print("\nYour bucket list")
            for i, bucket in enumerate(bucket_names):
                print(
                    ConsoleColors.BOLD + "  [" + str(i) + "]" + ConsoleColors.END_COLOR,
                    ConsoleColors.OK_GREEN + bucket + ConsoleColors.END_COLOR,
                )
            bucket_select = input(
                "\n"
                + ConsoleColors.BOLD
                + "select bucket(0-"
                + str(len(bucket_names) - 1)
                + "): "
                + ConsoleColors.END_COLOR
            )
            if bucket_select.strip() == "":
                print("Bye!")
                exit()
        print("============================================")

        bucket_name = bucket_names[int(bucket_select)]
        bucket = s3.Bucket(bucket_name)

        current_path = ""
        list_dir = print_folder(bucket, current_path)

        while True:
            cmd = input(
                ConsoleColors.OK_GREEN
                + "<"
                + bucket_name
                + "> "
                + ConsoleColors.END_COLOR
                + ConsoleColors.HEADER
                + "~/"
                + current_path
                + "$ "
                + ConsoleColors.END_COLOR
            )
            if cmd.startswith("!"):
                os.system(cmd[1:])
            elif cmd.startswith("l"):
                list_dir = print_folder(bucket, current_path, limit=-1)
                continue
            elif cmd.startswith("cd"):
                splited = cmd.split()
                if len(splited) != 2:
                    print("\n  usage: cd dir_name\n")
                    continue
                foldername = splited[1]
                if not foldername.endswith("/"):
                    foldername = foldername + "/"
                if foldername == "../":
                    current_path = current_path[: current_path.rfind("/", 0, -1) + 1]
                elif foldername == "~/":
                    current_path = ""
                elif foldername in list_dir:
                    current_path = current_path + foldername
                elif is_dir(bucket_name, foldername):
                    current_path = foldername
                else:
                    print(
                        ConsoleColors.FAIL,
                        "[FAIL] No such directory:",
                        foldername,
                    )
                    continue
                print("<" + bucket_name + "> ~/" + current_path + "$")
                list_dir = print_folder(bucket, current_path)
            elif cmd.startswith("up"):
                splited = cmd.split()
                if len(splited) not in [2, 3]:
                    print("\n  usage: up local_file [remote_name]\n")
                    continue
                filelist = glob(splited[1])
                if len(filelist) == 0:
                    print(
                        ConsoleColors.FAIL,
                        "[FAIL] No such file in local:",
                        cmd.split()[1],
                    )
                elif len(filelist) == 1:
                    filepath = filelist[0]
                    if len(splited) == 3:
                        filename = splited[2]
                    else:
                        filename = filepath.split("/")[-1]
                    bucket.Object(current_path + filename).upload_file(filepath)
                    print(ConsoleColors.OK_BLUE, "[SUCCESS] uploaded", filename)
                else:  # multiple file upload
                    if len(splited) == 3:
                        print(
                            ConsoleColors.FAIL,
                            "[FAIL] Cannot set remote_name if the matched local files are more than one",
                        )
                        print("\n  usage: up local_file [remote_name]\n")
                        continue
                    for filepath in filelist:
                        filename = filepath.split("/")[-1]
                        bucket.Object(current_path + filename).upload_file(filename)
                    print(
                        ConsoleColors.OK_BLUE,
                        "[SUCCESS] uploaded " + str(len(filelist)) + " files",
                    )
            elif cmd.startswith("down"):
                splited = cmd.split()
                if len(splited) not in [2, 3]:
                    print("\n  usage: down remote_file [local_name]\n")
                    continue
                filename = splited[1]
                get_name = filename
                if len(splited) >= 3:
                    get_name = splited[2]
                if filename in list_dir and not filename.endswith("/"):
                    bucket.Object(current_path + filename).download_file(get_name)
                    print(ConsoleColors.OK_BLUE, "[SUCCESS] downloaded ", get_name)
                else:
                    matched_list = fnmatch.filter(
                        filter(lambda x: not x.endswith('/'), list_dir),
                        filename,
                    )
                    if len(matched_list) > 0:  # multiple file download
                        if len(splited) >= 3:
                            print(
                                ConsoleColors.FAIL,
                                "[FAIL] Cannot set local_name if the matched remote files are more than one",
                            )
                            print("\n  usage: down remote_file [local_name]\n")
                            continue
                        print(
                            "downloading " + str(len(matched_list)) + " matched files"
                        )
                        for name in matched_list:
                            bucket.Object(current_path + name).download_file(name)
                        print(ConsoleColors.OK_BLUE, "[SUCCESS] done!")
                    else:
                        print(
                            ConsoleColors.FAIL,
                            "[FAIL] No such file in the current path:",
                            filename,
                        )
            elif cmd.startswith("mkdir"):
                splited = cmd.split()
                if len(splited) != 2:
                    print("\n  usage: mkdir dir_name\n")
                    continue
                new_folder_name = splited[1]
                if not new_folder_name.endswith('/'):
                    new_folder_name = new_folder_name + '/'
                if new_folder_name in list_dir:
                    print(
                        ConsoleColors.FAIL,
                        "[FAIL] There is already a directory with the same name:",
                        new_folder_name,
                    )
                else:
                    bucket.put_object(Key=current_path + new_folder_name)
                    list_dir = print_folder(bucket, current_path)
            elif cmd.startswith("rm"):
                splited = cmd.split()
                if len(splited) != 2:
                    print("\n  usage: rm file_or_dir_name\n")
                    continue
                filename = splited[1]
                if not filename.endswith('/') and filename in list_dir:
                    if (
                        input(
                            "  Are you sure you want to delete "
                            + filename
                            + "? (y/n) "
                        ).lower()
                        == "y"
                    ):
                        bucket.Object(current_path + filename).delete()
                        print("deleted " + filename)
                        list_dir = print_folder(bucket, current_path)
                elif (filename.endswith('/') and filename in list_dir) or filename + '/' in list_dir:
                    if not filename.endswith('/'):
                        filename = filename + '/'
                    if (
                        input(
                            "  '"
                            + filename
                            + "' is a directory. Are you sure you want to delete it? (y/n) "
                        ).lower()
                        == "y"
                    ):
                        cnt = 0
                        for obj in bucket.objects.filter(Prefix=current_path + filename):
                            length = obj.size 
                            obj.delete()
                            if length > 0:
                                cnt += 1
                        print("deleted " + str(cnt) + " files")
                        list_dir = print_folder(bucket, current_path)
                else:
                    matched_list = fnmatch.filter(
                        filter(lambda x: not x.endswith('/'), list_dir),
                        filename,
                    )
                    if len(matched_list) > 0:
                        if (
                            input(
                                "  Are you sure you want to delete "
                                + str(len(matched_list))
                                + " file(s)? (y/n) "
                            ).lower()
                            == "y"
                        ):
                            for name in matched_list:
                                bucket.Object(current_path + name).delete()
                            print("deleted " + str(len(matched_list)) + " files")
                            list_dir = print_folder(bucket, current_path)
                    else:
                        print(
                            ConsoleColors.FAIL,
                            "[FAIL] No such file in the current path:",
                            filename,
                        )
            elif cmd.startswith("exit") or cmd.startswith("q"):
                break
            elif cmd.strip() == "":
                continue
            else:
                print(
                    "\n  commands : cd, l=ls, mkdir, rm, up=upload, down=download, q=exit\n"
                )

    except KeyboardInterrupt:
        pass

    print("\nBye :)")


if __name__ == "__main__":
    main()
