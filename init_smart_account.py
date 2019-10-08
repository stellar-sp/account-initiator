import os
from stellar_base.horizon import Horizon
import requests
from stellar_base.operation import *
from stellar_base.transaction import Transaction
from stellar_base.transaction_envelope import TransactionEnvelope as Te
from stellar_base.keypair import Keypair
from environs import Env
import json

if os.path.exists('./.env'):
    env = Env()
    env.read_env(path="./.env")

HORIZON_ADDRESS = os.environ.get('HORIZON_ADDRESS')
FRIENDBOT_ADDRESS = os.environ.get('FRIENDBOT_ADDRESS')
NETWORK_PASSPHRASE = os.environ.get('NETWORK_PASSPHRASE')
SMART_PROGRAM_IMAGE_ADDRESS = os.environ.get('SMART_PROGRAM_IMAGE_ADDRESS')
SMART_PROGRAM_IMAGE_HASH = os.environ.get('SMART_PROGRAM_IMAGE_HASH')
EXECUTION_BASE_FEE = os.environ.get('EXECUTION_BASE_FEE')

SMART_ACCOUNT_ADDRESS = os.environ.get('SMART_ACCOUNT_ADDRESS')
SMART_ACCOUNT_SECRET_KEY = os.environ.get('SMART_ACCOUNT_SECRET_KEY')
WORKER_ADDRESSES = json.loads(os.environ.get('WORKER_ADDRESSES'))


horizon = Horizon(HORIZON_ADDRESS)

print('creating and funding accounts ...')
for worker_address in WORKER_ADDRESSES:
    requests.get(FRIENDBOT_ADDRESS + '/?addr=' + worker_address['public_key'])
    print("funded worker account: " + worker_address['public_key'])

requests.get(FRIENDBOT_ADDRESS + '/?addr=' + SMART_ACCOUNT_ADDRESS)
print("funded smart account: " + SMART_ACCOUNT_ADDRESS)


def sign_and_submit(ops):
    sequence = horizon.account(SMART_ACCOUNT_ADDRESS).get('sequence')

    tx = Transaction(
        source=SMART_ACCOUNT_ADDRESS,
        sequence=int(sequence),
        fee=1000 * len(ops),
        operations=ops
    )

    envelope = Te(tx=tx, network_id=NETWORK_PASSPHRASE)
    envelope.sign(Keypair.from_seed(SMART_ACCOUNT_SECRET_KEY))

    horizon.submit(envelope.xdr())


sign_and_submit([SetOptions(master_weight=100)])

operations = []
for worker_address in WORKER_ADDRESSES:
    operations.append(SetOptions(signer_address=worker_address['public_key'], signer_weight=1))
sign_and_submit(operations)

percent51 = int(len(WORKER_ADDRESSES)/2) + 1
sign_and_submit([SetOptions(low_threshold=percent51, med_threshold=percent51, high_threshold=percent51)])

sign_and_submit([ManageData('smart_program_image_address', SMART_PROGRAM_IMAGE_ADDRESS), ManageData(
    'execution_base_fee', EXECUTION_BASE_FEE), ManageData('smart_program_image_hash', SMART_PROGRAM_IMAGE_HASH)])

operations = []
counter = 1
for worker_address in WORKER_ADDRESSES:
    operations.append(ManageData('worker_' + str(counter) + '_address', worker_address['address']))
    counter += 1

counter = 1
for worker_address in WORKER_ADDRESSES:
    operations.append(ManageData('worker_' + str(counter) + '_public_key', worker_address['public_key']))
    counter += 1
sign_and_submit(operations)

sign_and_submit([SetOptions(master_weight=0)])
