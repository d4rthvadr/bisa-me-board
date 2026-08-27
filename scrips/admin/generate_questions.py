#!/usr/bin/env python3
import argparse
import os
import random
import sys
from pathlib import Path

import django


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def parse_args():
    parser = argparse.ArgumentParser(
        description='Generate disposable questions for a target board.',
    )
    parser.add_argument(
        '--board-code',
        required=True,
        help='Board code to seed questions for (example: ab12cd34).',
    )
    parser.add_argument(
        '--count',
        type=int,
        default=25,
        help='Number of questions to create (default: 25).',
    )
    parser.add_argument(
        '--nickname-prefix',
        default='Seeder',
        help='Nickname prefix used when creating questions (default: Seeder).',
    )
    parser.add_argument(
        '--max-votes',
        type=int,
        default=20,
        help='Maximum random vote_count assigned per generated question (default: 20).',
    )
    return parser.parse_args()


def bootstrap_django():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qna_board.settings')
    django.setup()


def main():
    args = parse_args()
    if args.count <= 0:
        raise ValueError('--count must be greater than 0.')
    if args.max_votes < 0:
        raise ValueError('--max-votes must be 0 or greater.')

    bootstrap_django()

    from board.models import Board, Question

    board = Board.objects.filter(code=args.board_code).first()
    if not board:
        raise ValueError(f'Board not found for code "{args.board_code}".')

    payload = []
    for index in range(1, args.count + 1):
        payload.append(
            Question(
                board=board,
                nickname=f'{args.nickname_prefix}-{index}',
                text=f'Disposable seeded question #{index} for board {board.code}',
                vote_count=random.randint(0, args.max_votes),
            )
        )

    Question.objects.bulk_create(payload)
    print(f'Created {len(payload)} questions for board "{board.title}" ({board.code}).')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'Error: {exc}', file=sys.stderr)
        raise SystemExit(1) from exc
