# Odoo 19 Controllers & Routes Reference

Hướng dẫn viết Controllers (HTTP routes) trong Odoo 19.

## 1. Basic Controller Structure

```python
from odoo import http
from odoo.http import request, Response
import json

class TrcfController(http.Controller):
    
    @http.route('/trcf/hello', type='http', auth='public', website=True)
    def hello_world(self):
        return "Hello TRCF!"
    
    @http.route('/trcf/order/<int:order_id>', type='http', auth='user')
    def get_order(self, order_id):
        order = request.env['trcf.order'].browse(order_id)
        return request.render('trcf_module.order_template', {'order': order})
```

## 2. Route Parameters

```python
@http.route(
    '/trcf/api/orders',
    type='json',           # 'http' or 'json'
    auth='user',           # 'public', 'user', 'none'
    methods=['GET', 'POST'],
    cors='*',              # CORS policy
    csrf=False,            # Disable CSRF for API
    website=False,         # True for website pages
    sitemap=False,         # Include in sitemap
    allow_frames=True,     # Allow iframe embed
)
def api_orders(self, **kwargs):
    pass
```

## 3. Auth Types

```python
# Public - No login required
@http.route('/public/page', auth='public')

# User - Must be logged in
@http.route('/private/page', auth='user')

# None - No auth check, access request.env as sudo
@http.route('/api/webhook', auth='none', csrf=False)
def webhook(self):
    # Must use sudo() for database operations
    request.env['model'].sudo().action()
```

## 4. HTTP Routes (type='http')

```python
@http.route('/trcf/form', type='http', auth='user', website=True, methods=['GET', 'POST'])
def order_form(self, **post):
    if request.httprequest.method == 'POST':
        # Handle form submission
        order = request.env['trcf.order'].create({
            'name': post.get('name'),
            'amount': float(post.get('amount', 0)),
        })
        return request.redirect(f'/trcf/order/{order.id}')
    
    # GET - render form
    return request.render('trcf_module.order_form', {
        'partners': request.env['res.partner'].search([]),
    })
```

### Response Types

```python
# Render QWeb template
return request.render('template.name', values)

# Redirect
return request.redirect('/target/url')
return request.redirect('/target/url', code=301)  # Permanent

# JSON response
return Response(
    json.dumps({'status': 'ok'}),
    content_type='application/json',
)

# File download
return request.make_response(
    file_content,
    headers=[
        ('Content-Type', 'application/pdf'),
        ('Content-Disposition', 'attachment; filename="report.pdf"'),
    ],
)

# Plain text
return Response("Plain text", content_type='text/plain')
```

## 5. JSON Routes (type='json')

```python
@http.route('/trcf/api/orders', type='json', auth='user', methods=['POST'])
def get_orders(self, domain=None, limit=100):
    """
    Called via: rpc('/trcf/api/orders', {domain: [...], limit: 50})
    """
    domain = domain or []
    orders = request.env['trcf.order'].search_read(
        domain,
        fields=['name', 'amount', 'state'],
        limit=limit,
    )
    return {'orders': orders, 'count': len(orders)}

@http.route('/trcf/api/create', type='json', auth='user')
def create_order(self, name, amount, partner_id=None):
    order = request.env['trcf.order'].create({
        'name': name,
        'amount': amount,
        'partner_id': partner_id,
    })
    return {'id': order.id, 'name': order.name}
```

## 6. Request Object

```python
# Current environment (database)
env = request.env

# Current user
user = request.env.user

# HTTP request details
method = request.httprequest.method  # 'GET', 'POST'
url = request.httprequest.url
path = request.httprequest.path
headers = request.httprequest.headers
cookies = request.httprequest.cookies

# Query parameters (GET)
param = request.params.get('param_name')

# Form data (POST)
data = request.httprequest.form.get('field_name')

# JSON body (type='json')
# Params are passed as function arguments

# Session
request.session['key'] = 'value'
value = request.session.get('key')

# Database
request.cr  # Cursor
request.db  # Database name
```

## 7. Error Handling

```python
from werkzeug.exceptions import NotFound, Forbidden, BadRequest

@http.route('/trcf/order/<int:order_id>', type='http', auth='user')
def get_order(self, order_id):
    order = request.env['trcf.order'].browse(order_id)
    
    if not order.exists():
        raise NotFound("Đơn hàng không tồn tại")
    
    if order.company_id != request.env.company:
        raise Forbidden("Bạn không có quyền truy cập")
    
    return request.render('template', {'order': order})

# JSON error response
@http.route('/api/action', type='json', auth='user')
def api_action(self, **kwargs):
    try:
        result = self._process(kwargs)
        return {'success': True, 'data': result}
    except Exception as e:
        return {'success': False, 'error': str(e)}
```

## 8. File Upload

```python
@http.route('/trcf/upload', type='http', auth='user', methods=['POST'], csrf=False)
def upload_file(self, **post):
    file = post.get('file')
    if file:
        # file.read() returns bytes
        content = file.read()
        filename = file.filename
        
        # Save as attachment
        attachment = request.env['ir.attachment'].create({
            'name': filename,
            'datas': base64.b64encode(content),
            'res_model': 'trcf.order',
            'res_id': post.get('order_id'),
        })
        
        return request.redirect('/success')
    
    return request.redirect('/error')
```

## 9. Website Integration

```python
@http.route('/shop/product/<int:product_id>', type='http', auth='public', website=True)
def product_page(self, product_id, **kwargs):
    product = request.env['product.product'].sudo().browse(product_id)
    
    return request.render('trcf_module.product_page', {
        'product': product,
        'main_object': product,  # For SEO
    })
```

### QWeb Template

```xml
<template id="product_page" name="Product Page">
    <t t-call="website.layout">
        <div class="container py-4">
            <h1 t-field="product.name"/>
            <p t-field="product.description"/>
            <span t-field="product.list_price" t-options="{'widget': 'monetary'}"/>
        </div>
    </t>
</template>
```

## 10. CORS & Security

```python
# Enable CORS for all origins
@http.route('/api/public', type='json', auth='public', cors='*', csrf=False)

# Specific origin
@http.route('/api/partner', type='json', auth='user', cors='https://partner.com')

# Webhook (no CSRF, no auth)
@http.route('/webhook/payment', type='json', auth='none', csrf=False)
def payment_webhook(self, **data):
    # Verify signature
    if not self._verify_signature(data):
        raise Forbidden("Invalid signature")
    
    # Process with sudo
    request.env['payment.transaction'].sudo().process(data)
    return {'status': 'ok'}
```
