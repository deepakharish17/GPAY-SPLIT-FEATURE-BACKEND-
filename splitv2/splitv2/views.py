from django.db import transaction
from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
from .models import User, wallets, split, split_Members, transactions, settlement, NetBalance, SettlementLedger
import json

def _ledger_entry(settlement_obj, entry_type, delta, remaining, original_amount, note=''):
    SettlementLedger.objects.create(
        settlement=settlement_obj,
        debtor=settlement_obj.payer,
        creditor=settlement_obj.receiver,
        entry_type=entry_type,
        original_amount=original_amount,
        delta=delta,
        remaining_amount=remaining,
        note=note,
    )


def close_split_if_completed(split_id):
    pending = split_Members.objects.filter(split_id=split_id, payment_status='PENDING').exists()
    if not pending:
        split.objects.filter(id=split_id).exclude(status='INACTIVE').update(status='INACTIVE')


def _mark_split_member_paid(settlement_obj, user):
    split_Members.objects.filter(
        split=settlement_obj.split,
        user=user,
        payment_status='PENDING',
    ).update(payment_status='PAID')


def _close_settlement(settlement_obj, close_parent_split=True):
    settlement_obj.status = 'PAID'
    settlement_obj.save()
    _mark_split_member_paid(settlement_obj, settlement_obj.payer)
    if close_parent_split:
        close_split_if_completed(settlement_obj.split_id)


def update_net_balance(debtor, creditor, amount, new_settlement_obj):
    reverse_nb = NetBalance.objects.filter(debtor=creditor, creditor=debtor).first()
    if not reverse_nb:
        nb, _ = NetBalance.objects.get_or_create(
            debtor=debtor,
            creditor=creditor,
            defaults={'amount': Decimal('0.00')},
        )
        nb.amount += amount
        nb.save()
        _ledger_entry(
            new_settlement_obj,
            entry_type='SPLIT_CREATED',
            delta=amount,
            remaining=amount,
            original_amount=amount,
            note='New debt created',
        )
        return
    offset_budget = amount
    reverse_settlements = settlement.objects.filter(
        payer=creditor,
        receiver=debtor,
        status='PENDING',
    ).order_by('id')
    for rev_s in reverse_settlements:
        if offset_budget <= Decimal('0.00'):
            break
        pre_amount = rev_s.amount
        if pre_amount <= offset_budget:
            offset_budget -= pre_amount
            rev_s.amount = Decimal('0.00')
            _ledger_entry(
                rev_s,
                entry_type='NET_OFFSET',
                delta=-pre_amount,
                remaining=Decimal('0.00'),
                original_amount=pre_amount,
                note=f'Fully consumed while offsetting new split (budget used={pre_amount})',
            )
            _close_settlement(rev_s, close_parent_split=True)
        else:
            rev_s.amount -= offset_budget
            rev_s.save()
            _ledger_entry(
                rev_s,
                entry_type='PARTIAL_OFFSET',
                delta=-offset_budget,
                remaining=rev_s.amount,
                original_amount=pre_amount,
                note=f'Partially consumed while offsetting new split (offset={offset_budget})',
            )
            offset_budget = Decimal('0.00')
    consumed = amount - offset_budget
    if consumed > Decimal('0.00'):
        if reverse_nb.amount <= consumed:
            reverse_nb.delete()
        else:
            reverse_nb.amount -= consumed
            reverse_nb.save()
    if offset_budget <= Decimal('0.00'):
        _ledger_entry(
            new_settlement_obj,
            entry_type='NET_OFFSET',
            delta=-amount,
            remaining=Decimal('0.00'),
            original_amount=amount,
            note='New debt fully offset by existing reverse NetBalance',
        )
        _close_settlement(new_settlement_obj, close_parent_split=False)
    else:
        new_settlement_obj.amount = offset_budget
        new_settlement_obj.save()
        _ledger_entry(
            new_settlement_obj,
            entry_type='PARTIAL_OFFSET',
            delta=-(amount - offset_budget),
            remaining=offset_budget,
            original_amount=amount,
            note=f'Partially offset by reverse NetBalance; remaining={offset_budget}',
        )
        nb, _ = NetBalance.objects.get_or_create(
            debtor=debtor,
            creditor=creditor,
            defaults={'amount': Decimal('0.00')},
        )
        nb.amount += offset_budget
        nb.save()


@csrf_exempt
def add_user(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    try:
        data = json.loads(request.body)
        username = data.get('user')
        if not username:
            return JsonResponse({'error': 'user name is required'}, status=400)
        user = User.objects.create(username=username)
        return JsonResponse({'id': user.id, 'user': username, 'message': 'User added!'}, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
def add_money(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        amount = Decimal(str(data.get('amount')))
        user = User.objects.get(id=user_id)
        wallet, _ = wallets.objects.get_or_create(user=user)
        wallet.balance += amount
        wallet.save()
        transactions.objects.create(
            sender=user,
            receiver=user,
            amount=amount,
            Transactions_type='WALLET_TOPUP',
            description='Wallet Top up'
        )
        return JsonResponse({
            'message': 'Money added successfully',
            'user': user.username,
            'amount_added': str(amount),
            'current_balance': str(wallet.balance),
        }, status=200)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
def add_splits(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    try:
        data = json.loads(request.body)
        amount = Decimal(str(data.get('amount')))
        description = data.get('description')
        split_type = data.get('split_type', 'EQUAL')
        status_val = data.get('status', 'ACTIVE')
        created_by = data.get('created_by')
        members = data.get('members', [])
        if not created_by or not members:
            return JsonResponse({'error': 'created_by and members list are required'}, status=400)
        if created_by in members:
            return JsonResponse({'error': 'creator should not be included in members list'}, status=400)
        if amount <= 0:
            return JsonResponse({'error': 'amount must be greater than 0'}, status=400)
        if len(set(members)) != len(members):
            return JsonResponse({'error': 'duplicate members are not allowed'}, status=400)
        with transaction.atomic():
            creator = User.objects.get(id=created_by)
            wallet_obj = wallets.objects.select_for_update().get(user=creator)
            if wallet_obj.balance < amount:
                return JsonResponse({'error': 'insufficient funds'}, status=400)
            wallet_obj.balance -= amount
            wallet_obj.save()
            split_obj = split.objects.create(
                total_amount=amount,
                description=description,
                Split_type=split_type,
                status=status_val,
                created_by=creator,
            )
            transactions.objects.create(
                sender=creator,
                receiver=creator,
                amount=amount,
                Transactions_type='EXPENSE',
                description=f'Creator paid expense for Split #{split_obj.id}'
            )
            total_people = len(members) + 1
            share_amount = (amount / Decimal(total_people)).quantize(Decimal('0.01'))
            split_Members.objects.create(
                split=split_obj,
                user=creator,
                share_amount=share_amount,
                payment_status='PAID',
            )
            for member_id in members:
                member = User.objects.get(id=member_id)
                split_Members.objects.create(
                    split=split_obj,
                    user=member,
                    share_amount=share_amount,
                    payment_status='PENDING',
                )
                settlement_obj = settlement.objects.create(
                    split=split_obj,
                    payer=member,
                    receiver=creator,
                    amount=share_amount,
                    status='PENDING',
                )
                update_net_balance(
                    debtor=member,
                    creditor=creator,
                    amount=share_amount,
                    new_settlement_obj=settlement_obj,
                )
            close_split_if_completed(split_obj.id)
        return JsonResponse({
            'message': 'Split created successfully',
            'split_id': split_obj.id,
            'total_amount': str(amount),
            'per_person_share': str(share_amount),
        }, status=201)
    except User.DoesNotExist:
        return JsonResponse({'error': 'One or more users do not exist'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
def remove_split(request):
    if request.method != 'DELETE':
        return HttpResponseNotAllowed(['DELETE'])
    try:
        split_id = request.GET.get('split_id')
        split_obj = split.objects.get(id=split_id)
        split_obj.delete()
        return JsonResponse({'message': 'Split Deleted Successfully'}, status=200)
    except split.DoesNotExist:
        return JsonResponse({'error': 'Split Not Found'}, status=404)


@csrf_exempt
def split_payment(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        split_id = data.get('split_id')

        with transaction.atomic():
            split_members_obj = split_Members.objects.select_for_update().get(
                split_id=split_id,
                user_id=user_id,
            )
            if split_members_obj.payment_status == 'PAID':
                return JsonResponse({'error': 'Payment Already Completed'}, status=400)
            split_obj = split.objects.get(id=split_id)
            try:
                settlement_obj = settlement.objects.select_for_update().get(
                    split_id=split_id,
                    payer_id=user_id,
                    receiver_id=split_obj.created_by.id,
                    status='PENDING',
                )
            except settlement.DoesNotExist:
                split_members_obj.payment_status = 'PAID'
                split_members_obj.save()
                close_split_if_completed(split_id)
                split_obj.refresh_from_db()
                return JsonResponse({
                    'message': 'Settlement already cleared via net offset. Member marked paid.',
                    'split_id': split_id,
                    'user_id': user_id,
                    'amount_paid': '0.00',
                    'split_status': split_obj.status,
                }, status=200)
            amount_to_pay = settlement_obj.amount
            payer_wallet = wallets.objects.select_for_update().get(user_id=user_id)
            creator_wallet = wallets.objects.select_for_update().get(user=split_obj.created_by)
            if payer_wallet.balance < amount_to_pay:
                return JsonResponse({'error': 'Insufficient Funds'}, status=400)
            payer_wallet.balance -= amount_to_pay
            payer_wallet.save()
            creator_wallet.balance += amount_to_pay
            creator_wallet.save()
            first_ledger = settlement_obj.ledger_entries.order_by('created_at').first()
            original_amount = first_ledger.original_amount if first_ledger else amount_to_pay
            settlement_obj.amount = Decimal('0.00')
            settlement_obj.status = 'PAID'
            settlement_obj.save()
            _ledger_entry(
                settlement_obj,
                entry_type='PAYMENT',
                delta=-amount_to_pay,
                remaining=Decimal('0.00'),
                original_amount=original_amount,
                note=f'Cash payment of {amount_to_pay} via split_payment endpoint',
            )
            split_members_obj.payment_status = 'PAID'
            split_members_obj.save()
            transaction_obj = transactions.objects.create(
                sender_id=user_id,
                receiver_id=split_obj.created_by.id,
                amount=amount_to_pay,
                Transactions_type='SPLIT_PAYMENT',
                description=f'Split Payment For Split #{split_id}',
            )
            net_balance = NetBalance.objects.filter(
                debtor_id=user_id,
                creditor_id=split_obj.created_by.id,
            ).first()
            if net_balance:
                if net_balance.amount <= amount_to_pay:
                    net_balance.delete()
                else:
                    net_balance.amount -= amount_to_pay
                    net_balance.save()
            close_split_if_completed(split_id)
            split_obj.refresh_from_db()
            payer_wallet.refresh_from_db()
            creator_wallet.refresh_from_db()

        return JsonResponse({
            'message': 'Payment Successful',
            'split_id': split_id,
            'user_id': user_id,
            'amount_paid': str(amount_to_pay),
            'wallet_balance': str(payer_wallet.balance),
            'creator_balance': str(creator_wallet.balance),
            'transaction_id': transaction_obj.id,
            'settlement_id': settlement_obj.id,
            'split_status': split_obj.status,
        }, status=200)
    except split_Members.DoesNotExist:
        return JsonResponse({'error': 'Split Member Not Found'}, status=404)
    except wallets.DoesNotExist:
        return JsonResponse({'error': 'Wallet Not Found'}, status=404)
    except split.DoesNotExist:
        return JsonResponse({'error': 'Split Not Found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_all_split_by_user(request):
    if request.method !='GET':
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)
    user_id = request.GET.get('user_id')
    try:
        if not user_id:
            return JsonResponse({'error': 'User Not Found'}, status=404)
        settlements = settlement.objects.filter(payer_id=user_id, status='PENDING').select_related('split', 'receiver')
        data = []
        total_amount = Decimal('0.00')
        for obj in settlements:
            data.append({
                'user_id': user_id,
                "split_id": obj.split.id,
                "description": obj.split.description,
                "created_by": obj.receiver.username,
                "amount_to_pay": str(obj.amount),
                "split_status": obj.split.status,
                "created_at": obj.split.created_at,
            })
            total_amount += obj.amount
        return JsonResponse({
            "Total amount": str(total_amount),
            "total pending split": len(data),
            "splits": data
        }, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def pay_multiple_splits(request):
    if request.method !='POST':
        return JsonResponse({'error': 'Method Not Allowed'}, status=405)
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        split_ids = data.get('split_ids',[])
        if not user_id or not split_ids:
            return JsonResponse({'error': 'User and split ids are required'}, status=404)
        with transaction.atomic():
            payer_wallet = wallets.objects.select_for_update().get( user_id=user_id)
            settlements=settlement.objects.filter(
                payer_id=user_id,
                split_id__in=split_ids,
                status='PENDING',
            ).select_related('split', 'receiver')
            if not settlements.exists():
                return JsonResponse({
                    'error':"No Settlement pending found"
                },status=404)
            total_amount = Decimal('0.00')
            for obj in settlements:
                total_amount+=obj.amount
            if payer_wallet.balance < total_amount:
                return JsonResponse({
                    'Message':"Insufficient Balance",
                    'required fund': total_amount,
                    'Balance':payer_wallet.balance
                },status=404)
            completed=[]
            for obj in settlements:
                creator_wallet = wallets.objects.select_for_update().get(user=obj.receiver.id)
                payment_amount = obj.amount

                payer_wallet.balance -= payment_amount
                payer_wallet.save()
                creator_wallet.balance += payment_amount
                creator_wallet.save()

                obj.status = 'PAID'
                obj.amount = Decimal("0.00")
                obj.save()

                split_member = split_Members.objects.get(split=obj.split, user_id=user_id)
                split_member.payment_status = 'PAID'
                split_member.save()
                _ledger_entry(
                    obj,
                    entry_type='PAYMENT',
                    original_amount=payment_amount,
                    delta=-payment_amount,
                    remaining=Decimal(0.00),
                    note='Bulk Split Payment',
                )
                transactions.objects.create(
                    sender_id=user_id,
                    receiver=obj.receiver,
                    Transactions_type='Split Payment',
                    amount=payment_amount,
                    description="Bulk Split Payment"
                )
                nb = NetBalance.objects.filter(
                    debtor_id=user_id,
                    creditor_id=obj.receiver.id,
                ).first()
                if nb:
                    if nb.amount <= payment_amount:
                        nb.delete()
                    else:
                        nb.amount -= payment_amount
                        nb.save()
                close_split_if_completed(obj.split_id)

                completed.append({
                    "split_id": obj.split_id,
                    "amount": str(payment_amount),
                })
            payer_wallet.refresh_from_db()
            return JsonResponse({
                "message": "Payment Successful",
                "total_paid": str(total_amount),
                "wallet balance": str(payer_wallet.balance),
                "completed splits": completed,
            })
    except wallets.DoesNotExist:
        return JsonResponse(
            {
                "error": "Wallet Not Found"
            },status=404)
    except Exception as e:
        return JsonResponse(
            {
                "error": str(e)
            },status=500)