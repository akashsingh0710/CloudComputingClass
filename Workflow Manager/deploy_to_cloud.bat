::pscp requires putty
pscp -pwfile pwfile.txt .\workflow_manager.py .\workflow_router.py .\network_config.json generic@csa-6343-103.utdallas.edu:/home/generic/Desktop/
pscp -pwfile pwfile.txt .\workflow_router.py generic@csa-6343-93.utdallas.edu:/home/generic/Desktop/
pscp -pwfile pwfile.txt .\workflow_router.py pvm1@10.176.67.248:/home/pvm1/Desktop/
pscp -pwfile pwfile.txt .\workflow_router.py pvm2@10.176.67.247:/home/pvm2/Desktop/
pscp -pwfile pwfile.txt .\workflow_router.py pvm3@10.176.67.246:/home/pvm3/Desktop/
pscp -pwfile pwfile.txt .\workflow_router.py pvm4@10.176.67.245:/home/pvm4/Desktop/