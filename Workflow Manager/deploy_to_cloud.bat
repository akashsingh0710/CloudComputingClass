::pscp requires putty
::currently deploys to deploy-test directory on Desktop
pscp -pwfile pwfile.txt .\workflow_manager.py .\workflow_router.py .\network_config.json generic@csa-6343-93.utdallas.edu:/home/generic/Desktop/deploy-test/
pscp -pwfile pwfile.txt .\workflow_router.py .\network_config.json generic@csa-6343-103.utdallas.edu:/home/generic/Desktop/deploy-test/
pscp -pwfile pwfile.txt .\workflow_router.py .\network_config.json pvm1@10.176.67.248:/home/pvm1/Desktop/deploy-test/
pscp -pwfile pwfile.txt .\workflow_router.py .\network_config.json pvm2@10.176.67.247:/home/pvm2/Desktop/deploy-test/
pscp -pwfile pwfile.txt .\workflow_router.py .\network_config.json pvm3@10.176.67.246:/home/pvm3/Desktop/deploy-test/
pscp -pwfile pwfile.txt .\workflow_router.py .\network_config.json pvm4@10.176.67.245:/home/pvm4/Desktop/deploy-test/