from django.db import transaction
from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
from .models import User, wallets, split, split_Members, transactions, settlement, NetBalance
import json


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
        wallet, created = wallets.objects.get_or_create(user=user)
        wallet.balance += amount
        wallet.save()
        transactions.objects.create(
            sender=user,
            receiver=user,
            amount=amount,
            Transactions_type='WALLET_PAYMENT',
            description='Wallet Top up'
        )
        return JsonResponse({
            "message": "Money added successfully",
            "user": user.username,
            "amount_added": str(amount),
            "current_balance": str(wallet.balance)
        }, status=200)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


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
            return JsonResponse(
                {'error': 'created_by and members list are required'},
                status=400
            )
        if created_by in members:
            return JsonResponse(
                {'error': 'Creator should not be included in members list'},
                status=400
            )
        if amount <= 0:
            return JsonResponse(
                {'error': 'Amount must be greater than 0'},
                status=400
            )
        if len(set(members)) != len(members):
            return JsonResponse(
                {'error': 'Duplicate members are not allowed'},
                status=400
            )
        wallet_id=wallets.objects.get(user=created_by)
        wallet_id.balance -=amount
        wallet_id.save()
        with transaction.atomic():
            creator = User.objects.get(id=created_by)
            split_obj = split.objects.create(
                total_amount=amount,
                description=description,
                Split_type=split_type,
                status=status_val,
                created_by=creator
            )
            total_people = len(members) + 1
            share_amount = (
                amount / Decimal(total_people)
            ).quantize(Decimal('0.01'))
            split_Members.objects.create(
                split=split_obj,
                user=creator,
                share_amount=share_amount,
                payment_status='PAID'
            )
            for member_id in members:
                member = User.objects.get(id=member_id)
                split_Members.objects.create(
                    split=split_obj,
                    user=member,
                    share_amount=share_amount,
                    payment_status='PENDING'
                )
                settlement.objects.create(
                    split=split_obj,
                    payer=member,
                    receiver=creator,
                    amount=share_amount,
                    status='PENDING'
                )
                update_net_balance(
                    debtor=member,
                    creditor=creator,
                    amount=share_amount
                )
        return JsonResponse(
            {
                'message': 'Split created successfully',
                'split_id': split_obj.id,
                'total_amount': str(amount),
                'per_person_share': str(share_amount)
            },
            status=201
        )
    except User.DoesNotExist:
        return JsonResponse(
            {'error': 'One or more users do not exist'},
            status=404
        )
    except Exception as e:
        return JsonResponse(
            {'error': str(e)},
            status=400
        )


@csrf_exempt
def remove_split(request):
    if request.method != 'DELETE':
        return HttpResponseNotAllowed(['DELETE'])
    try:
        split_id = request.GET.get('split_id')
        split_obj = split.objects.get(id=split_id)
        split_obj.delete()
        return JsonResponse({"message": "Split Deleted Successfully"}, status=200)
    except split.DoesNotExist:
        return JsonResponse({"error": "Split Not Found"}, status=404)


@csrf_exempt
def split_payment(request):

    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        split_id = data.get('split_id')
        split_members_obj = split_Members.objects.get(
            split_id=split_id,
            user_id=user_id
        )
        split_obj = split.objects.get(id=split_id)
        share_amount = split_members_obj.share_amount
        split_wallet_obj = wallets.objects.get(user_id=user_id)
        creator_wallet = wallets.objects.get(
            user=split_obj.created_by
        )
        if split_members_obj.payment_status == 'PAID':
            return JsonResponse(
                {"error": "Payment Already Completed"},
                status=400
            )
        if split_wallet_obj.balance < share_amount:
            return JsonResponse(
                {"error": "Insufficient Funds"},
                status=400
            )
        with transaction.atomic():
            split_wallet_obj.balance -= share_amount
            split_wallet_obj.save()
            creator_wallet.balance += share_amount
            creator_wallet.save()
            split_members_obj.payment_status = 'PAID'
            split_members_obj.save()
            close_split_if_completed(split_id)
            settlement_obj = settlement.objects.get(
                split_id=split_id,
                payer_id=user_id,
                receiver_id=split_obj.created_by.id,
                status='PENDING'
            )
            settlement_obj.status = 'PAID'
            settlement_obj.save()
            transaction_obj = transactions.objects.create(
                sender_id=user_id,
                receiver_id=split_obj.created_by.id,
                amount=share_amount,
                Transactions_type='SPLIT_PAYMENT',
                description=f'Split Payment For Split #{split_id}'
            )
            net_balance = NetBalance.objects.filter(
                debtor_id=user_id,
                creditor_id=split_obj.created_by.id
            ).first()
            if net_balance:
                if net_balance.amount <= share_amount:
                    net_balance.delete()
                else:
                    net_balance.amount -= share_amount
                    net_balance.save()
            unpaid_settlement = settlement.objects.filter(
                split_id=split_id,
                status='PENDING'
            ).exists()
            if not unpaid_settlement:
                split_obj.status = 'INACTIVE'
                split_obj.save()
        return JsonResponse({
            "message": "Payment Successful",
            "split_id": split_id,
            "user_id": user_id,
            "amount_paid": str(share_amount),
            "wallet_balance": str(split_wallet_obj.balance),
            "creator_balance": str(creator_wallet.balance),
            "transaction_id": transaction_obj.id,
            "settlement_id": settlement_obj.id,
            "split_status": split_obj.status
        }, status=200)
    except split_Members.DoesNotExist:
        return JsonResponse({"error": "Split Member Not Found"},status=404)
    except settlement.DoesNotExist:
        return JsonResponse({"error": "Settlement Not Found"}, status=404)
    except wallets.DoesNotExist:
        return JsonResponse({"error": "Wallet Not Found"},  status=404)
    except split.DoesNotExist:
        return JsonResponse({"error": "Split Not Found"}, status=404)
    except Exception as e:
        return JsonResponse( {"error": str(e)}, status=500)


def close_split_if_completed(split_id):

    pending = split_Members.objects.filter(
        split_id=split_id,
        payment_status='PENDING'
    ).exists()
    if not pending:
        split_obj = split.objects.get(id=split_id)
        split_obj.status = 'INACTIVE'
        split_obj.save()

def update_net_balance(debtor, creditor, amount):
    reverse = NetBalance.objects.filter(
        debtor=creditor,
        creditor=debtor
    ).first()
    if reverse:
        # CASE 1
        if reverse.amount > amount:
            if reverse.amount > amount:
                reverse.amount -= amount
                reverse.save()
                # UPDATE THE OLD SETTLEMENT AMOUNT
                remaining_settlement = settlement.objects.filter(
                    payer=creditor,
                    receiver=debtor,
                    status='PENDING'
                ).first()
                if remaining_settlement:
                    remaining_settlement.amount -= amount
                    remaining_settlement.save()
                settlement_to_close = settlement.objects.filter(
                    payer=debtor,
                    receiver=creditor,
                    status='PENDING'
                ).first()
                if settlement_to_close:
                    settlement_to_close.status = 'PAID'
                    settlement_to_close.save()
                    split_member = split_Members.objects.filter(
                        split=settlement_to_close.split,
                        user=debtor
                    ).first()
                    if split_member:
                        split_member.payment_status = 'PAID'
                        split_member.save()
                    pending_members = split_Members.objects.filter(
                        split=settlement_to_close.split,
                        payment_status='PENDING'
                    ).exists()
                    if not pending_members:
                        settlement_to_close.split.status = 'INACTIVE'
                        settlement_to_close.split.save()
                return
            settlement_to_close = settlement.objects.filter(
                payer=debtor,
                receiver=creditor,
                status='PENDING'
            ).first()
            if settlement_to_close:
                settlement_to_close.status = 'PAID'
                settlement_to_close.save()
                split_member = split_Members.objects.filter(
                    split=settlement_to_close.split,
                    user=debtor
                ).first()
                if split_member:
                    split_member.payment_status = 'PAID'
                    split_member.save()
                pending_members = split_Members.objects.filter(
                    split=settlement_to_close.split,
                    payment_status='PENDING'
                ).exists()
                if not pending_members:
                    settlement_to_close.split.status = 'INACTIVE'
                    settlement_to_close.split.save()
            return
        # CASE 2
        elif reverse.amount == amount:
            settlement_1 = settlement.objects.filter(
                payer=debtor,
                receiver=creditor,
                status='PENDING'
            ).first()
            settlement_2 = settlement.objects.filter(
                payer=creditor,
                receiver=debtor,
                status='PENDING'
            ).first()
            if settlement_1:
                settlement_1.status = 'PAID'
                settlement_1.save()
                member_1 = split_Members.objects.filter(
                    split=settlement_1.split,
                    user=debtor
                ).first()
                if member_1:
                    member_1.payment_status = 'PAID'
                    member_1.save()
            if settlement_2:
                settlement_2.status = 'PAID'
                settlement_2.save()
                member_2 = split_Members.objects.filter(
                    split=settlement_2.split,
                    user=creditor
                ).first()
                if member_2:
                    member_2.payment_status = 'PAID'
                    member_2.save()
            for obj in [settlement_1, settlement_2]:
                if obj:
                    pending = split_Members.objects.filter(
                        split=obj.split,
                        payment_status='PENDING'
                    ).exists()
                    if not pending:
                        obj.split.status = 'INACTIVE'
                        obj.split.save()
            reverse.delete()
            return
        # CASE 3
        else:
            remaining = amount - reverse.amount
            settlement_to_close = settlement.objects.filter(
                payer=creditor,
                receiver=debtor,
                status='PENDING'
            ).first()
            if settlement_to_close:
                settlement_to_close.status = 'PAID'
                settlement_to_close.save()
                split_member = split_Members.objects.filter(
                    split=settlement_to_close.split,
                    user=creditor
                ).first()
                if split_member:
                    split_member.payment_status = 'PAID'
                    split_member.save()
                pending_members = split_Members.objects.filter(
                    split=settlement_to_close.split,
                    payment_status='PENDING'
                ).exists()
                if not pending_members:
                    settlement_to_close.split.status = 'INACTIVE'
                    settlement_to_close.split.save()
            reverse.delete()
            NetBalance.objects.create(
                debtor=debtor,
                creditor=creditor,
                amount=remaining
            )
            return
    else:
        existing = NetBalance.objects.filter(
            debtor=debtor,
            creditor=creditor
        ).first()
        if existing:
            existing.amount += amount
            existing.save()
        else:
            NetBalance.objects.create(
                debtor=debtor,
                creditor=creditor,
                amount=amount
            )


