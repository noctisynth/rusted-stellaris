"""Generate named planets, preserving their impact and occupation mechanics.

This legacy entry point delegates to the complete state generator.
"""

from make_planet_states import main
from localization import synchronize

if __name__ == "__main__":
    main()
    synchronize(write=True)
