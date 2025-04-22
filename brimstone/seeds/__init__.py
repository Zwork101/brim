from asyncio import create_task, gather
from collections import namedtuple
from importlib import import_module
import logging
from pathlib import Path
import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

seed_directory = Path(__file__).parent
Seed = namedtuple("Seed", "module function priority")


def get_seeds() -> list[Seed]:
    seeds = []

    for root, _, files in os.walk(seed_directory):
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                
                route_module = import_module('.'.join(('seeds', *Path(root).relative_to(seed_directory).parts)) + "." + file[:-3])
                
                module_priority = route_module.__dict__.get("__priority__")
                if module_priority is None:
                    logging.warning(f"Module priority for seed: '{route_module.__name__}' not set. Defaulting to 1000.")
                    module_priority = 1000
                                
                if "operations" in route_module.__dict__:
                    operations = route_module.operations()
                    for operation in operations:
                        if isinstance(operation, tuple):
                            seeds.append(Seed(
                                route_module,
                                operation[0],
                                module_priority + operation[1]
                            ))
                        else:
                            seeds.append(Seed(
                                route_module,
                                operation,
                                module_priority
                            ))
                else:
                    logging.warning(f"Seeding module '{route_module.__name__}' does not contain 'operations' method.")
    
    return seeds

def group_seeds(*seeds: Seed):
    sorted_seeds = [*sorted(seeds, key=lambda x: x.priority)]
    grouped_seeds: list[list[Seed]] = []
    for seed in sorted_seeds:
        if len(grouped_seeds) == 0 or grouped_seeds[-1][0].priority != seed.priority:
            grouped_seeds += [[seed]]
        else:
            grouped_seeds[-1].append(seed)
    return grouped_seeds

async def plant_seeds(session_maker: async_sessionmaker[AsyncSession], *seeds: Seed) -> None:
    async with session_maker.begin() as session:
        tasks = []
        for seed in seeds:
            tasks.append(create_task(seed.function(session)))
        await gather(*tasks)    
        await session.commit()
