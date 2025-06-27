#Riley O'Shea
#University of Colorado Colorado Springs
#06/25/2025


#runs the scripts in the correct order to manage audit

import pullModules
import youtubeVideo


def main():
    print("Debug: Starting audit")
    pullModules.main()
    youtubeVideo.main()
    print("Debug: Audit completed successfully")


if __name__ == "__main__":
    main()