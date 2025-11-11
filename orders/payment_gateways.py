from abc import ABC, abstractmethod
from django.utils.translation import gettext_lazy as _
import random
import time

class PaymentGateway(ABC):
    """Abstract base class for payment gateways"""
    
    @abstractmethod
    def process_payment(self, amount, phone_number, order_reference):
        pass
    
    @abstractmethod
    def get_gateway_name(self):
        pass

class MpesaGateway(PaymentGateway):
    """M-Pesa Payment Gateway"""
    
    def process_payment(self, amount, phone_number, order_reference):
        # Simulate M-Pesa payment processing
        time.sleep(2)  # Simulate API call
        
        # Simulate random success/failure
        success = random.random() > 0.2  # 80% success rate
        
        if success:
            return {
                'success': True,
                'transaction_id': f'MPESA{random.randint(100000, 999999)}',
                'message': _('Payment processed successfully via M-Pesa')
            }
        else:
            return {
                'success': False,
                'error': _('M-Pesa payment failed. Please try again.')
            }
    
    def get_gateway_name(self):
        return 'M-Pesa'

class TigoPesaGateway(PaymentGateway):
    """Tigo Pesa Payment Gateway"""
    
    def process_payment(self, amount, phone_number, order_reference):
        time.sleep(2)
        success = random.random() > 0.15  # 85% success rate
        
        if success:
            return {
                'success': True,
                'transaction_id': f'TIGO{random.randint(100000, 999999)}',
                'message': _('Payment processed successfully via Tigo Pesa')
            }
        else:
            return {
                'success': False,
                'error': _('Tigo Pesa payment failed. Please try again.')
            }
    
    def get_gateway_name(self):
        return 'Tigo Pesa'

class AirtelMoneyGateway(PaymentGateway):
    """Airtel Money Payment Gateway"""
    
    def process_payment(self, amount, phone_number, order_reference):
        time.sleep(2)
        success = random.random() > 0.1  # 90% success rate
        
        if success:
            return {
                'success': True,
                'transaction_id': f'AIRTEL{random.randint(100000, 999999)}',
                'message': _('Payment processed successfully via Airtel Money')
            }
        else:
            return {
                'success': False,
                'error': _('Airtel Money payment failed. Please try again.')
            }
    
    def get_gateway_name(self):
        return 'Airtel Money'

class SelcomGateway(PaymentGateway):
    """Selcom Payment Gateway"""
    
    def process_payment(self, amount, phone_number, order_reference):
        time.sleep(3)  # Selcom is slower
        success = random.random() > 0.25  # 75% success rate
        
        if success:
            return {
                'success': True,
                'transaction_id': f'SELCOM{random.randint(100000, 999999)}',
                'message': _('Payment processed successfully via Selcom')
            }
        else:
            return {
                'success': False,
                'error': _('Selcom payment failed. Please try again.')
            }
    
    def get_gateway_name(self):
        return 'Selcom'

class PaymentGatewayFactory:
    """Factory class to create payment gateway instances"""
    
    @staticmethod
    def get_gateway(gateway_name):
        gateways = {
            'mpesa': MpesaGateway,
            'tigopesa': TigoPesaGateway,
            'airtelmoney': AirtelMoneyGateway,
            'selcom': SelcomGateway,
        }
        
        gateway_class = gateways.get(gateway_name.lower())
        if gateway_class:
            return gateway_class()
        raise ValueError(_('Unsupported payment gateway'))