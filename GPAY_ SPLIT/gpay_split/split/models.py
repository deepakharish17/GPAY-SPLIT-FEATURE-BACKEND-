from django.db import models
class User(models.Model):
    username = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username
    class Meta:
        db_table = 'user'

class wallets(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE,related_name='wallets')
    balance=models.DecimalField(max_digits=12,decimal_places=2,default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} Wallet"
    class Meta:
        db_table = 'wallets'

class transactions(models.Model):
    Transactions_type=(
    ('Transfer','TRANSFER'),
    ('SPLIT_PAYMENT','Split payment'),
    ('WALLET_PAYMENT','Wallet payment'),)
    sender=models.ForeignKey(User,on_delete=models.CASCADE,related_name='sender')
    receiver=models.ForeignKey(User,on_delete=models.CASCADE,related_name='receiver')
    amount=models.DecimalField(max_digits=12,decimal_places=2,default=0)
    Transactions_type=models.CharField(choices=Transactions_type,max_length=100)
    description=models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}-{self.receiver}-{self.amount}"
    class Meta:
        db_table = 'transactions'

class split(models.Model):
    Split_type=(
    ('EQUAL','Equal'),
    ('CUSTOM','Custom'),)
    Status_type=(
    ('ACTIVE','Active'),
    ('INACTIVE','Inactive'),)
    created_by=models.ForeignKey(User,on_delete=models.CASCADE,related_name='Created_splits')
    total_amount=models.DecimalField(max_digits=12,decimal_places=2,default=0)
    description=models.TextField()
    Split_type=models.CharField(choices=Split_type,max_length=100,default='EQUAL')
    created_at = models.DateTimeField(auto_now_add=True)
    status=models.CharField(choices=Status_type,max_length=100,default='ACTIVE')

    def __str__(self):
        return f"{self.id}-{self.description}"
    class Meta:
        db_table = 'splits'

class split_Members(models.Model):
    payment_status=(
        ('CREDIT', 'Credit'),
        ('DEBIT', 'Debit'),
        ('SPLIT_PAYMENT', 'Split Payment'),
        ('SETTLEMENT_ADJUSTMENT', 'Settlement Adjustment'),
        ('SPLIT_CREATED', 'Split Created'),)
    split=models.ForeignKey(split,on_delete=models.CASCADE,related_name='members')
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    share_amount=models.DecimalField(max_digits=12,decimal_places=2,default=0)
    payment_status=models.CharField(choices=payment_status,max_length=100,default='PENDING')
    Joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.split}"
    class Meta:
        db_table = 'split_members'

class settlement(models.Model):
    Status_type=(
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),)
    split=models.ForeignKey(split,on_delete=models.CASCADE,related_name='settlements')
    payer=models.ForeignKey(User,on_delete=models.CASCADE,related_name='payments_made')
    receiver=models.ForeignKey(User,on_delete=models.CASCADE,related_name='payments_received')
    amount=models.DecimalField(max_digits=12,decimal_places=2)
    payed_at=models.DateTimeField(auto_now_add=True)
    status=models.CharField(choices=Status_type,max_length=100,default='PENDING')

    def __str__(self):
        return f"{self.payer} - {self.receiver}-{self.amount}"
    class Meta:
        db_table = 'settlements'

class NetBalance(models.Model):
    debtor = models.ForeignKey( User, on_delete=models.CASCADE,related_name='debts')
    creditor = models.ForeignKey( User, on_delete=models.CASCADE,related_name='credits')
    amount = models.DecimalField(max_digits=12,decimal_places=2,default=0)

    class Meta:
        db_table = 'net_balances'
        constraints = [models.UniqueConstraint( fields=['debtor', 'creditor'],name='unique_debtor_creditor')]


# class SettlementLedger(models.Model):
#
#     settlement = models.ForeignKey(settlement,on_delete=models.CASCADE,related_name="ledger_entries")
#     debtor = models.ForeignKey(User,on_delete=models.CASCADE,related_name="ledger_debtor")
#     creditor = models.ForeignKey(User,on_delete=models.CASCADE,related_name="ledger_creditor")
#     original_amount = models.DecimalField(max_digits=12,decimal_places=2)
#     remaining_amount = models.DecimalField(max_digits=12,decimal_places=2)
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     class Meta:
#         db_table = "settlement_ledger"