import argparse
import asyncio
from collections import defaultdict
from pathlib import Path
from uuid import UUID

from sqlalchemy import delete, select, text

from app.infrastructure.database import AsyncSessionFactory
from app.models.database import Resume, ScreeningResult


def choose_resume_to_keep(resumes: list[Resume]) -> Resume:
    return sorted(
        resumes,
        key=lambda item: (
            item.parse_status != "parsed",
            item.created_at,
            str(item.id),
        ),
    )[0]


async def cleanup_duplicates(apply: bool) -> None:
    async with AsyncSessionFactory() as session:
        rows = list(
            (
                await session.execute(
                    select(Resume)
                    .where(Resume.file_hash.is_not(None))
                    .order_by(Resume.position_id, Resume.file_hash, Resume.created_at)
                )
            )
            .scalars()
            .all()
        )

        groups: dict[tuple[UUID, str], list[Resume]] = defaultdict(list)
        for resume in rows:
            if resume.file_hash:
                groups[(resume.position_id, resume.file_hash)].append(resume)

        duplicates: list[Resume] = []
        for (position_id, file_hash), items in groups.items():
            if len(items) <= 1:
                continue
            kept = choose_resume_to_keep(items)
            removed = [item for item in items if item.id != kept.id]
            duplicates.extend(removed)
            print(
                f"{position_id} {file_hash}: keep {kept.id} ({kept.file_name}), "
                f"remove {len(removed)} duplicate(s)"
            )
            for item in removed:
                print(f"  - {item.id} {item.file_name} {item.parse_status} {item.created_at}")

        if not duplicates:
            print("No duplicate resumes found.")
            return

        if not apply:
            print(f"Dry run only. Re-run with --apply to remove {len(duplicates)} duplicate resume(s).")
            return

        duplicate_ids = [item.id for item in duplicates]
        duplicate_paths = [Path(item.file_path) for item in duplicates]

        await session.execute(delete(ScreeningResult).where(ScreeningResult.resume_id.in_(duplicate_ids)))
        table_exists = await session.scalar(text("select to_regclass('public.langchain_pg_embedding')"))
        if table_exists:
            for resume_id in duplicate_ids:
                await session.execute(
                    text("delete from langchain_pg_embedding where cmetadata ->> 'resume_id' = :resume_id"),
                    {"resume_id": str(resume_id)},
                )
        for item in duplicates:
            await session.delete(item)
        await session.commit()

    for path in duplicate_paths:
        try:
            if path.exists():
                path.unlink()
        except Exception as exc:
            print(f"Could not delete file {path}: {exc}")

    print(f"Removed {len(duplicate_ids)} duplicate resume(s).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Remove duplicate resumes by position_id + file_hash.")
    parser.add_argument("--apply", action="store_true", help="Actually delete duplicates. Omit for dry-run.")
    args = parser.parse_args()
    asyncio.run(cleanup_duplicates(apply=args.apply))


if __name__ == "__main__":
    main()
