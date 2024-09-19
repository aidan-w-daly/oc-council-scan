from app import *


def main():
    for meeting in get_last_cc_all():
        pdf_to_txt(meeting)
    print('main done')

if __name__ == '__main__':
    main()