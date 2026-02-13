import os

mode = os.getenv("PIPELINE_MODE", "discovery")

if mode == "enrichment":
    from zcap.enrichment_runner import main
else:
    from zcap.run import main

if __name__ == "__main__":
    main()