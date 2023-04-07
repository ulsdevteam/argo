window.drf = {
    csrfHeaderName: "{{ csrf_header_name|default:'X-CSRFToken' }}",
    csrfCookieName: "{{ csrf_cookie_name|default:'csrftoken' }}"
};