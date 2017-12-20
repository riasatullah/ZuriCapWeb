# By: Riasat Ullah

# database errors
error_db_connection = 'Failed to connect to the database'
error_db_disconnection = 'Failed to disconnect from the database'
error_db_query = 'Database query failed'

# login error
error_loging_failed = 'Login query failed'
error_login_incorrect = 'Incorrect credentials were provided'
error_login_missing = 'Please provide all login details'
error_password_invalid = 'Invalid password - only alphanumeric accepted; ' +\
                         'must have at least 1 upper case, 1 lower case, 1 number; ' +\
                         'must be between 8 and 15 characters long.'
error_password_mismatch = 'Passwords do not match'

# client errors
error_book_financing = 'Failed to book financing at this time. Please try again.'
error_book_repayment = 'Failed to book repayment at this time. Please try again.'
error_client_add = 'Failed to add client at this time. Please try again.'
error_client_type_invalid = 'Invalid client type: Client is neither a buyer nor a supplier'
error_client_edit = 'Failed to edit client details at this time. Please try again.'
error_financing_amount = 'Amount is more than the remaining financing.'
error_financing_zero = 'Cannot accept 0 financing.'
error_repayment_amount = 'Amount is more than the remaining repayment.'
error_repayment_zero = 'Cannot accept 0 repayment.'
error_multiple_entries = 'Multiple entries found for the same day. Cannot process.'
error_page_failed = 'Failed to produce the desired page. Please try again later.'
error_relation_add = 'Failed to add relation at this time. Please try again.'
error_relation_edit = 'Failed to edit relation at this time. Please try again.'
error_save_limits = 'Failed to save new limits at this time. Please try again.'

error_invalid_date = 'Date is invalid'
error_invoice_description = 'Invoice description should be within 140 characters'
error_invoice_amount = 'Invoice amount is not valid'
error_invalid_payee = 'Invalid payee provided for repayment'

msg_invoice_success = 'Your invoice has been uploaded'
msg_limits_saved = 'New limits have been saved successfully'
msg_password_updated = 'Your password has been updated'
msg_payment_booked = 'Payment was booked successfully.'


def limit_breach(limit_type, current_val, breach_val):
    msg = 'Limit breach - {0} - Current: {1} | Proposed: {2}'
    return msg.format(limit_type, current_val, breach_val)
