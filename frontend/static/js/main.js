/* A kids — Global deferred JavaScript (loaded with defer) */

// ===== Global Lazy Loading: Intersection Observer for scroll animations =====
document.addEventListener('DOMContentLoaded', function() {
    var observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-visible');
                observer.unobserve(entry.target);
            }
        });
    }, {
        rootMargin: '50px',
        threshold: 0.05
    });

    document.querySelectorAll('.fade-in-section, .fade-in-card').forEach(function(el) {
        observer.observe(el);
    });

    // Skeleton grid swap: hide skeletons, show real grids
    document.querySelectorAll('.skeleton-grid').forEach(function(el) {
        el.style.display = 'none';
    });
    document.querySelectorAll('.real-grid').forEach(function(el) {
        el.style.display = '';
    });

    document.querySelectorAll('.img-blur-load').forEach(function(img) {
        if (img.complete) {
            img.classList.add('loaded');
        } else {
            img.addEventListener('load', function() {
                this.classList.add('loaded');
            });
        }
    });
});

// ===== Autocomplete Search =====
function initAutocomplete(inputEl) {
    if (!inputEl || inputEl.dataset.acInitialized) return;
    inputEl.dataset.acInitialized = '1';

    var wrapper = inputEl.closest('.search-wrapper');
    if (!wrapper) return;
    var dropdown = wrapper.querySelector('.autocomplete-dropdown');
    if (!dropdown) return;
    var form = inputEl.closest('form');
    var categoryInput = form ? form.querySelector('input[name="category"]') : null;
    var debounceTimer = null;
    var selectedIndex = -1;
    var currentResults = [];

    function fetchSuggestions(query) {
        if (query.length < 1) { dropdown.classList.remove('active'); dropdown.innerHTML = ''; return; }
        dropdown.innerHTML = '<div class="autocomplete-loading"><div class="dots"><span></span><span></span><span></span></div></div>';
        dropdown.classList.add('active');
        selectedIndex = -1;
        var params = new URLSearchParams({ q: query });
        if (categoryInput && categoryInput.value) params.set('category', categoryInput.value);
        fetch('/api/search-suggestions/?' + params.toString())
            .then(function(r) { return r.json(); })
            .then(function(data) {
                currentResults = data.results || [];
                renderDropdown(currentResults, query);
            })
            .catch(function() { dropdown.classList.remove('active'); });
    }

    function renderDropdown(results, query) {
        if (!results.length) {
            dropdown.innerHTML = '<div class="autocomplete-empty">No products found</div>';
            dropdown.classList.add('active'); return;
        }
        var html = '';
        for (var i = 0; i < results.length; i++) {
            var r = results[i];
            html += '<a href="' + r.url + '" class="autocomplete-item" data-index="' + i + '">'
                + '<img src="' + r.image + '" alt="" loading="lazy" onerror="this.style.display=\'none\'">'
                + '<div class="item-info">'
                + '<div class="item-name">' + highlightMatch(r.name, query) + '</div>'
                + '<div class="item-price">\u20B9' + r.price + '</div>'
                + '</div></a>';
        }
        dropdown.innerHTML = html;
        dropdown.classList.add('active');
    }

    function highlightMatch(text, query) {
        if (!query) return escapeHtml(text);
        var escaped = escapeHtml(text);
        var safeQuery = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        var re = new RegExp('(' + safeQuery + ')', 'gi');
        return escaped.replace(re, '<strong style="color:#6698CC">$1</strong>');
    }

    function escapeHtml(str) {
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }

    function selectItem(index) {
        var items = dropdown.querySelectorAll('.autocomplete-item');
        if (index >= 0 && index < items.length) window.location.href = items[index].getAttribute('href');
    }

    function highlightItem(index) {
        var items = dropdown.querySelectorAll('.autocomplete-item');
        items.forEach(function(el) { el.classList.remove('highlighted'); });
        if (index >= 0 && index < items.length) items[index].classList.add('highlighted');
    }

    inputEl.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        var val = this.value.trim();
        if (val.length >= 1) {
            debounceTimer = setTimeout(function() { fetchSuggestions(val); }, 200);
        } else {
            dropdown.classList.remove('active'); dropdown.innerHTML = '';
        }
    });

    inputEl.addEventListener('keydown', function(e) {
        var items = dropdown.querySelectorAll('.autocomplete-item');
        if (e.key === 'ArrowDown') { e.preventDefault(); selectedIndex = Math.min(selectedIndex + 1, items.length - 1); highlightItem(selectedIndex); }
        else if (e.key === 'ArrowUp') { e.preventDefault(); selectedIndex = Math.max(selectedIndex - 1, -1); highlightItem(selectedIndex); }
        else if (e.key === 'Enter') { if (selectedIndex >= 0 && items.length > 0) { e.preventDefault(); selectItem(selectedIndex); } }
        else if (e.key === 'Escape') { dropdown.classList.remove('active'); selectedIndex = -1; }
    });

    inputEl.addEventListener('blur', function() { setTimeout(function() { dropdown.classList.remove('active'); }, 200); });
    inputEl.addEventListener('focus', function() {
        if (currentResults.length > 0 || this.value.trim().length >= 1) {
            if (currentResults.length > 0) dropdown.classList.add('active');
            else if (this.value.trim().length >= 1) fetchSuggestions(this.value.trim());
        }
    });
}

document.addEventListener('DOMContentLoaded', function() {
    var inputs = document.querySelectorAll('.search-wrapper input[name="q"]');
    for (var i = 0; i < inputs.length; i++) { initAutocomplete(inputs[i]); }
});

function toggleMobileMenu() {
    var drawer = document.getElementById('mobileDrawer');
    if (!drawer) return;
    if (drawer.classList.contains('hidden')) {
        drawer.classList.remove('hidden'); drawer.style.display = 'flex';
    } else {
        drawer.classList.add('hidden'); drawer.style.display = 'none';
    }
}

function togglePassword(inputId, iconId) {
    var input = document.getElementById(inputId);
    var icon = document.getElementById(iconId);
    if (input.type === 'password') { input.type = 'text'; icon.textContent = 'visibility_off'; }
    else { input.type = 'password'; icon.textContent = 'visibility'; }
}

var mohanlalHistory = [];

function toggleMohanlalChat() {
    var modal = document.getElementById('mohanlalChatModal');
    if (!modal) return;
    if (modal.classList.contains('hidden')) {
        modal.classList.remove('hidden');
        setTimeout(function() { var inp = document.getElementById('mohanlalChatInput'); if (inp) inp.focus(); }, 100);
    } else { modal.classList.add('hidden'); }
}

async function sendMohanlalMessage(e) {
    e.preventDefault();
    var input = document.getElementById('mohanlalChatInput');
    var msgBox = document.getElementById('mohanlalChatMessages');
    var sendBtn = document.getElementById('mohanlalSendBtn');
    var text = input.value.trim();
    if (!text) return;
    input.value = ''; input.disabled = true; sendBtn.disabled = true;

    var userDiv = document.createElement('div');
    userDiv.className = 'flex items-start justify-end gap-2';
    userDiv.innerHTML = '<div class="bg-tangerine text-white p-3 rounded-2xl rounded-tr-md shadow-sm max-w-[85%] text-sm">' + text.replace(/</g, "&lt;").replace(/>/g, "&gt;") + '</div>';
    msgBox.appendChild(userDiv);
    msgBox.scrollTop = msgBox.scrollHeight;

    var loadingDiv = document.createElement('div');
    loadingDiv.id = 'mohanlalLoading';
    loadingDiv.className = 'flex items-start gap-2';
    loadingDiv.innerHTML = '<div class="w-7 h-7 rounded-full bg-tangerine text-white flex items-center justify-center text-xs font-bold shrink-0">M</div><div class="bg-white p-3 rounded-2xl rounded-tl-md shadow-sm text-on-surface flex items-center gap-1.5"><span class="w-2 h-2 bg-tangerine rounded-full animate-bounce"></span><span class="w-2 h-2 bg-tangerine rounded-full animate-bounce" style="animation-delay:0.2s"></span><span class="w-2 h-2 bg-tangerine rounded-full animate-bounce" style="animation-delay:0.4s"></span></div>';
    msgBox.appendChild(loadingDiv);
    msgBox.scrollTop = msgBox.scrollHeight;

    try {
        var res = await fetch('/api/chat/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text, history: mohanlalHistory })
        });
        var data = await res.json();
        var lDiv = document.getElementById('mohanlalLoading');
        if (lDiv) lDiv.remove();
        var reply = data.reply || "I am having a little connectivity trouble right now. For urgent queries or larger requirements, please call us at 9924343003!";
        mohanlalHistory.push({ role: "user", content: text });
        mohanlalHistory.push({ role: "assistant", content: reply });
        var formattedReply = reply.replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\n/g, "<br>");
        formattedReply = formattedReply.replace(/(9924343003)/g, '<a href="tel:9924343003" class="font-extrabold text-tangerine underline">$1</a>');
        formattedReply = formattedReply.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
        var botDiv = document.createElement('div');
        botDiv.className = 'flex items-start gap-2';
        botDiv.innerHTML = '<div class="w-7 h-7 rounded-full bg-tangerine text-white flex items-center justify-center text-xs font-bold shrink-0">M</div><div class="bg-white p-3 rounded-2xl rounded-tl-md shadow-sm max-w-[85%] text-on-surface text-sm leading-relaxed"><p class="font-semibold text-xs text-tangerine mb-1">Mohanlal</p><div>' + formattedReply + '</div></div>';
        msgBox.appendChild(botDiv);
        msgBox.scrollTop = msgBox.scrollHeight;
    } catch (err) {
        var lDiv = document.getElementById('mohanlalLoading');
        if (lDiv) lDiv.remove();
        var errDiv = document.createElement('div');
        errDiv.className = 'flex items-start gap-2';
        errDiv.innerHTML = '<div class="w-7 h-7 rounded-full bg-tangerine text-white flex items-center justify-center text-xs font-bold shrink-0">M</div><div class="bg-white p-3 rounded-2xl rounded-tl-md shadow-sm max-w-[85%] text-on-surface text-sm"><p class="font-semibold text-xs text-tangerine mb-1">Mohanlal</p><p>Oops! Network issue. For larger queries or immediate help, please call us directly at <a href="tel:9924343003" class="font-bold text-tangerine underline">9924343003</a>.</p></div>';
        msgBox.appendChild(errDiv);
        msgBox.scrollTop = msgBox.scrollHeight;
    } finally {
        input.disabled = false; sendBtn.disabled = false; input.focus();
    }
}

// --- GLOBAL DROPDOWN SYSTEM ---
var activeDropdownTimer = null;
var isTouchDevice = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);

function toggleNavDropdown(event, type) {
    event.stopPropagation();
    var btn = document.getElementById('nav-btn-' + type);
    var menu = document.getElementById('nav-menu-' + type);
    var isOpen = !menu.classList.contains('hidden');
    if (!isTouchDevice && isOpen) return;
    closeAllNavDropdowns();
    if (!isOpen) {
        menu.classList.remove('hidden');
        btn.setAttribute('aria-expanded', 'true');
        setTimeout(function() {
            menu.classList.remove('scale-95', 'opacity-0');
            menu.classList.add('scale-100', 'opacity-100');
        }, 10);
    }
}

function closeAllNavDropdowns() {
    var menus = document.querySelectorAll('[id^="nav-menu-"]');
    var btns = document.querySelectorAll('[id^="nav-btn-"]');
    menus.forEach(function(menu) {
        menu.classList.add('hidden', 'scale-95', 'opacity-0');
        menu.classList.remove('scale-100', 'opacity-100');
    });
    btns.forEach(function(btn) {
        btn.setAttribute('aria-expanded', 'false');
    });
}

function closeAllNavDropdownsExcept(activeMenu) {
    var menus = document.querySelectorAll('[id^="nav-menu-"]');
    var btns = document.querySelectorAll('[id^="nav-btn-"]');
    menus.forEach(function(menu) {
        if (menu !== activeMenu) {
            menu.classList.add('hidden', 'scale-95', 'opacity-0');
            menu.classList.remove('scale-100', 'opacity-100');
        }
    });
    btns.forEach(function(btn) {
        var type = btn.id.replace('nav-btn-', '');
        var correspondingMenu = document.getElementById('nav-menu-' + type);
        if (correspondingMenu !== activeMenu) {
            btn.setAttribute('aria-expanded', 'false');
        }
    });
}

function setupDropdownHover() {
    var containers = document.querySelectorAll('.nav-dropdown-container');
    containers.forEach(function(container) {
        var btn = container.querySelector('[id^="nav-btn-"]');
        var menu = container.querySelector('[id^="nav-menu-"]');
        container.addEventListener('mouseenter', function() {
            if (activeDropdownTimer) {
                clearTimeout(activeDropdownTimer);
                activeDropdownTimer = null;
            }
            closeAllNavDropdownsExcept(menu);
            if (menu.classList.contains('hidden')) {
                menu.classList.remove('hidden');
                btn.setAttribute('aria-expanded', 'true');
                setTimeout(function() {
                    menu.classList.remove('scale-95', 'opacity-0');
                    menu.classList.add('scale-100', 'opacity-100');
                }, 10);
            }
        });
        container.addEventListener('mouseleave', function() {
            if (activeDropdownTimer) clearTimeout(activeDropdownTimer);
            activeDropdownTimer = setTimeout(function() {
                closeAllNavDropdowns();
            }, 200);
        });
    });
}

document.addEventListener('DOMContentLoaded', setupDropdownHover);

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeAllNavDropdowns();
});

document.addEventListener('click', function(e) {
    if (!e.target.closest('.nav-dropdown-container')) closeAllNavDropdowns();
});

// ===== Toast System =====
function showToast(msgOrTitle, typeOrMsg, maybeType) {
    var message, type;
    if (maybeType !== undefined) { message = typeOrMsg; type = maybeType; }
    else { message = msgOrTitle; type = typeOrMsg || 'success'; }
    var container = document.getElementById('toast-container');
    var toast = document.createElement('div');
    var colorMap = {
        success: { bg: '#FFF8F0', border: '#F08C21', text: '#854500', icon: 'check_circle' },
        info:    { bg: '#E6F0FA', border: '#6698CC', text: '#1B3B5C', icon: 'info' },
        error:   { bg: '#FDECEF', border: '#E36888', text: '#7A1C33', icon: 'error' }
    };
    var colors = colorMap[type] || colorMap.success;
    toast.style.cssText = 'pointer-events:auto;display:flex;align-items:center;gap:12px;padding:14px 16px 14px 20px;border-radius:16px;box-shadow:0 10px 25px -5px rgba(0,0,0,.15),0 4px 10px -5px rgba(0,0,0,.1);border-left:4px solid '+colors.border+';background:'+colors.bg+';color:'+colors.text+';font-family:Quicksand,Plus Jakarta Sans,sans-serif;transform:translateX(120%);opacity:0;transition:transform .35s cubic-bezier(.22,1,.36,1),opacity .35s ease;';
    var iconEl = document.createElement('span');
    iconEl.className = 'material-symbols-outlined';
    iconEl.style.cssText = "font-size:20px;font-variation-settings:'FILL' 1;flex-shrink:0;";
    iconEl.textContent = colors.icon;
    toast.appendChild(iconEl);
    var msgEl = document.createElement('span');
    msgEl.style.cssText = 'font-size:13px;font-weight:700;line-height:1.4;flex:1;';
    msgEl.textContent = message;
    toast.appendChild(msgEl);
    var closeBtn = document.createElement('button');
    closeBtn.innerHTML = '&times;';
    closeBtn.style.cssText = 'background:none;border:none;cursor:pointer;color:'+colors.text+';opacity:.5;font-size:20px;line-height:1;padding:0 0 0 6px;flex-shrink:0;';
    closeBtn.setAttribute('aria-label', 'Dismiss');
    closeBtn.addEventListener('click', function() {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(40px)';
        setTimeout(function() { toast.remove(); }, 350);
    });
    toast.appendChild(closeBtn);
    container.appendChild(toast);
    requestAnimationFrame(function() {
        requestAnimationFrame(function() {
            toast.style.transform = 'translateX(0)';
            toast.style.opacity = '1';
        });
    });
    setTimeout(function() {
        if (toast.parentNode) {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(40px)';
            setTimeout(function() { toast.remove(); }, 350);
        }
    }, 4000);
}

// Auto-show toast from URL parameter
(function() {
    var params = new URLSearchParams(window.location.search);
    var t = params.get('toast');
    var msgs = {
        'added': ['Item added to cart', 'success'],
        'removed': ['Item removed from cart', 'success'],
        'updated': ['Cart updated', 'success'],
        'checkout': ['Redirecting to checkout...', 'info'],
        'login-required': ['Please log in before checking out.', 'info'],
        'out-of-stock': ['This product is out of stock.', 'error'],
        'unavailable': ['Remove unavailable items before checking out.', 'error'],
        'saved': ['Profile updated successfully!', 'success'],
        'login': ['Logged in successfully!', 'success'],
        'signup': ['Account created successfully!', 'success'],
        'logout': ['Logged out successfully', 'success']
    };
    if (t && msgs[t]) {
        showToast(msgs[t][0], msgs[t][1]);
        var url = new URL(window.location);
        url.searchParams.delete('toast');
        window.history.replaceState({}, '', url);
    }
})();

// Global scroll position preservation system
(function() {
    document.addEventListener('submit', function() {
        sessionStorage.setItem('scroll_position_' + window.location.pathname, window.scrollY);
    });
    window.addEventListener('beforeunload', function() {
        sessionStorage.setItem('scroll_position_' + window.location.pathname, window.scrollY);
    });
    function restoreScroll() {
        var savedScroll = sessionStorage.getItem('scroll_position_' + window.location.pathname);
        if (savedScroll !== null) {
            window.scrollTo({ top: parseInt(savedScroll, 10), behavior: 'instant' });
            sessionStorage.removeItem('scroll_position_' + window.location.pathname);
        }
    }
    document.addEventListener('DOMContentLoaded', restoreScroll);
    window.addEventListener('load', restoreScroll);
})();

// Left Navigation Sidebar and Accordion Drawer Toggle
function toggleLeftSidebar() {
    var sidebar = document.getElementById('leftSidebar');
    var backdrop = document.getElementById('leftSidebarBackdrop');
    if (sidebar.classList.contains('open')) {
        sidebar.classList.remove('open');
        backdrop.classList.add('hidden');
        document.body.style.overflow = '';
    } else {
        sidebar.classList.add('open');
        backdrop.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }
}

function toggleSidebarAccordion(id) {
    var content = document.getElementById(id);
    var icon = document.getElementById(id + '-icon');
    if (content.classList.contains('hidden')) {
        content.classList.remove('hidden');
        content.classList.add('flex');
        if (icon) icon.classList.add('rotate-180');
    } else {
        content.classList.add('hidden');
        content.classList.remove('flex');
        if (icon) icon.classList.remove('rotate-180');
    }
}
