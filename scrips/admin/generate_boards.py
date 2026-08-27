#!/usr/bin/env python3
import argparse
import os
import sys
from pathlib import Path

import django


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def parse_args():
    parser = argparse.ArgumentParser(
        description='Generate disposable boards for admin testing.',
    )
    parser.add_argument(
        '--count',
        type=int,
        default=10,
        help='Number of boards to create (default: 10).',
    )
    parser.add_argument(
        '--title-prefix',
        default='Seed Board',
        help='Board title prefix (default: Seed Board).',
    )
    parser.add_argument(
        '--owner-username',
        help='Optional owner username. If omitted, boards are created without an owner.',
    )
    parser.add_argument(
        '--status',
        choices=['active', 'closed'],
        default='active',
        help='Initial board status (default: active).',
    )
    return parser.parse_args()


def bootstrap_django():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qna_board.settings')
    django.setup()


def main():
    args = parse_args()
    if args.count <= 0:
        raise ValueError('--count must be greater than 0.')

    bootstrap_django()

    from django.contrib.auth import get_user_model
    from board.models import Board

    owner = None
    if args.owner_username:
        owner = get_user_model().objects.filter(username=args.owner_username).first()
        if not owner:
            raise ValueError(f'User not found for username "{args.owner_username}".')

    created = 0
    for index in range(1, args.count + 1):
        Board.objects.create(
            title=f'{args.title_prefix} #{index}',
            owner=owner,
            status=args.status,
        )
        created += 1
    owner_label = owner.username if owner else 'no owner'
    print(f'Created {created} boards ({args.status}) for {owner_label}.')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'Error: {exc}', file=sys.stderr)
        raise SystemExit(1) from exc
