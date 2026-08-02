# 👤 A kids Enterprise — User Manual

> **Version**: 1.0 · **Last Updated**: 2 August 2026  
> **Audience**: Customers and end users of the A kids Enterprise storefront  
> **Platform URL**: `https://akidsenterprise.com`

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [Browsing Products](#2-browsing-products)
3. [Product Details & Variant Selection](#3-product-details--variant-selection)
4. [Shopping Cart](#4-shopping-cart)
5. [Checkout & Placing Orders](#5-checkout--placing-orders)
6. [Order History & Invoices](#6-order-history--invoices)
7. [User Profile](#7-user-profile)
8. [Catalogue Inquiries](#8-catalogue-inquiries)
9. [AI Chat Assistant](#9-ai-chat-assistant)
10. [FAQs](#10-faqs)

---

## 1. Getting Started

### Creating an Account

You can create an account using any of these methods:

| Method | How |
|--------|-----|
| **Email & Password** | Click **Sign Up**, enter your name, email, and password (min 6 characters) |
| **Google Sign-In** | Click the **"Sign in with Google"** button on the login/signup page |
| **Passwordless (Magic Link)** | Enter your email and receive a sign-in link via email — no password needed |

### Logging In

1. Navigate to the **Login** page (click the profile icon in the navbar or visit `/login/`).
2. Enter your email and password, or use Google/Passwordless sign-in.
3. You will be redirected to the homepage.

> [!TIP]
> **Forgot your password?** Use the "Forgot Password" option on the login page. You'll receive a magic link via email to set a new password.

---

## 2. Browsing Products

### Navigation

Products are organized into categories accessible from the top navigation bar and homepage:

| Category | Description | Navigation |
|----------|-------------|------------|
| **Indoors** | Classroom furniture, desks, chairs, storage, educational aids | Click "Indoors" in navbar |
| **Outdoors** | Playground equipment, swings, slides, multi-play systems | Click "Outdoors" in navbar |
| **Shreem Sports** | Sports equipment and accessories (coming soon) | Click "Shreem Sports" in navbar |

### Product Cards

Each product card displays:
- **Product image** (hover for subtle zoom effect)
- **Product name**
- **Price** (with discount price if applicable)
- **Colour swatches** — small dots showing available colours
- **Dimension summary** — compact table showing available sizes
- **Class/Age group** — which standards the product fits

### Searching

Use the **search bar** in the navigation header:
1. Start typing a product name.
2. Live **search suggestions** appear as you type (product name, price, image thumbnail).
3. Click a suggestion to go directly to the product.
4. Press Enter to see full search results.

### Catalogue PDF Viewing

From the Indoor/Outdoor pages, you can view the full product **catalogue PDF** inline on the page. This is the same catalogue used by the sales team.

---

## 3. Product Details & Variant Selection

Click any product card to open the **Product Detail** page. Here you'll find:

### Product Information
- **Full-size product image**
- **Product name and SKU**
- **Price** with GST indication
- **Detailed description** (materials, safety specs, features)

### Variant Selection

Products may have two types of variants that you **must select** before adding to cart:

#### Colour Selection
- Colour swatches are displayed as clickable circles.
- Click a colour to select it — the swatch highlights with a ring.
- The selected colour name appears as a label.

#### Dimension Selection
- Dimensions are shown as clickable buttons.
- Each button displays the measurements (e.g., `60 × 45 × 59-90 cm`).
- If the product has components (e.g., Desk + Chair), the component name appears in the button.
- Click a dimension to select it.

### Specs Cards

Below the selectors, two information cards are displayed:

| Card | Contents |
|------|----------|
| **Class / Age Group** | Table showing which school standards and age ranges the product fits |
| **Product Dimensions** | Full specifications table with component, L×W×H, unit, and notes |

> [!IMPORTANT]
> You **must** select both a colour and a dimension (when available) before adding the product to your cart. If you try to add without selecting, a toast notification will prompt you.

---

## 4. Shopping Cart

### Adding Items

1. Select your colour and dimension on the product detail page.
2. Click **"Add to Cart"**.
3. A toast confirms the item has been added.

### Viewing Your Cart

Click the **cart icon** in the navigation header or visit `/cart/`.

Your cart displays:
- **Product image and name**
- **Colour badge** (if a colour was selected)
- **Dimension badge** (if a dimension was selected)
- **Unit price** and **line subtotal**
- **Quantity controls** (update or remove)

### Cart Behaviour

- The **same product** in **different colours or dimensions** appears as **separate line items**.
- You can update quantities or remove items individually.
- Cart items are **stock-aware** — you cannot add more than the available stock.
- Prices and totals update automatically.

---

## 5. Checkout & Placing Orders

### Checkout Process

1. From your cart, click **"Proceed to Checkout"**.
2. Fill in the checkout form:

| Field | Description |
|-------|-------------|
| **Full Name** | Your name for the order |
| **Shipping Address** | Delivery address (pre-filled from your saved default address if available) |
| **Phone Number** | Contact number for delivery |

3. Review your order summary:
   - All line items with colours and dimensions
   - **Subtotal** (before tax)
   - **GST** (18% added on top)
   - **Total** (final payable amount)

4. Click **"Place Order"**.

### After Placing an Order

- You'll be redirected to the **Order Success** page.
- Your order receives a sequential number (e.g., `ORD-00042`).
- Stock is **atomically decremented** — no overselling.
- You can view your order details and download the invoice PDF.

> [!NOTE]
> **GST Calculation**: All prices shown are **GST-exclusive**. 18% GST is calculated and added on top at checkout. The invoice PDF shows the full GST breakup.

---

## 6. Order History & Invoices

### Viewing Past Orders

Go to your **Profile** page (click the avatar in the navbar → Profile) to see your order history.

Each order shows:
- **Order number** and **date**
- **Status** (Placed → Confirmed → Packed → Shipped → Delivered)
- **Items** with colour and dimension badges
- **Total amount**

### Invoice PDF

From the order detail view, click **"Download Invoice"** to get a PDF invoice containing:
- Your details and shipping address
- Line items: product name, colour, dimension, quantity, unit price, subtotal
- Financial summary: subtotal, 18% GST, total payable
- Order number and date

---

## 7. User Profile

Access your profile from the **avatar icon** in the top-right corner of the navbar.

### Profile Features

| Feature | Description |
|---------|-------------|
| **Avatar Colour** | Choose from 12 preset colours for your profile avatar. Click the avatar to open the colour picker modal. Your selected colour appears across the site in your navbar avatar. |
| **Username** | Change your display username. Note: there is a **30-day cooldown** between username changes. |
| **Full Name** | Update your full name for orders and invoices. |
| **Phone Number** | Update your contact phone number. |
| **Change Password** | Open a modal to change your current password. Requires current password verification. |

### Saved Addresses

You can save up to **5 delivery addresses** for quick checkout:

1. On your profile page, find the **Saved Addresses** section.
2. Click **"Add Address"** to create a new address.
3. Fill in: Full Name, Phone, Street Address, City, State, Pincode.
4. Mark one address as **Default** — it will auto-fill during checkout.
5. Edit or delete addresses as needed.

---

## 8. Catalogue Inquiries

If you're interested in products from the **catalogue PDF** (especially for bulk orders or institutional purchases):

1. Navigate to a catalogue page (Indoor/Outdoor View All Products).
2. Fill in the **inquiry form** with:
   - Your **name** and **contact number**
   - **Email** (optional)
   - Select products from the catalogue list
   - Specify **quantities**
3. Submit the inquiry.
4. The A kids team will contact you via phone or WhatsApp.

> [!TIP]
> Catalogue inquiries are ideal for **schools and institutions** looking to furnish entire classrooms or playgrounds. You'll receive a custom quote from the sales team.

---

## 9. AI Chat Assistant

A friendly AI chat assistant is available on most pages (look for the floating chat bubble in the bottom-right corner).

- **Powered by**: Groq AI (Llama 3 model)
- **Personality**: The assistant is themed as "Mohanlal" — a helpful, friendly mascot
- **Capabilities**: Can answer questions about products, the company, safety standards, ordering process, and general playground equipment advice

> [!NOTE]
> The chat assistant is **not available** on the Admin HQ page. It is intended for customers browsing the storefront.

---

## 10. FAQs

### General

**Q: Do I need an account to browse products?**  
A: No, you can browse all products and catalogues without an account. An account is required for adding items to cart and placing orders.

**Q: What payment methods are accepted?**  
A: Currently, orders are placed as "test mode" orders. Full Razorpay payment integration is planned for a future release. Contact the sales team for payment arrangements.

### Products

**Q: What does "No Colour" mean?**  
A: Some products (like metal playground equipment) don't come in specific colour variants. When "No Colour" is indicated, the product comes in its standard finish.

**Q: Why do I need to select both colour and dimension?**  
A: Colour and dimension are variant attributes that determine the exact product you're ordering. They ensure you receive the correct size and colour.

**Q: What does the "Adjustable" height mean?**  
A: Some furniture (especially school desks) have adjustable height mechanisms. The dimension shows the range (e.g., `59-90 cm` means the height can be adjusted from 59cm to 90cm).

### Orders

**Q: How is GST calculated?**  
A: Prices listed on the website are **GST-exclusive**. 18% GST is added on top at checkout. For example, a ₹10,000 product will have ₹1,800 GST, totalling ₹11,800.

**Q: Can I cancel my order?**  
A: Please contact the A kids team directly at **+91 7433 026 008** or email **info@akidsenterprise.com** for order cancellations and returns.

**Q: Where can I see my order status?**  
A: Go to your Profile page to view all your past orders and their current status.

### Account

**Q: I forgot my password. What do I do?**  
A: Click "Forgot Password" on the login page. Enter your email address, and you'll receive a passwordless magic link to sign in. Once signed in, you can set a new password from your Profile page.

**Q: Why can't I change my username?**  
A: Usernames have a 30-day cooldown period. If you've changed your username recently, you'll need to wait 30 days before changing it again.

**Q: Can I have multiple saved addresses?**  
A: Yes, up to 5 addresses. Mark one as "Default" for automatic checkout pre-fill.

---

## Contact & Support

| Channel | Details |
|---------|---------|
| **Phone** | +91 7433 026 008 |
| **Email** | info@akidsenterprise.com |
| **WhatsApp** | +91 7433 026 008 |
| **Website** | https://akidsenterprise.com |

---

*End of User Manual. For admin-specific features, see the [Admin Manual](admin_manual.md).*
