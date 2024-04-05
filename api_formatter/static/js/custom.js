// Handles clicks on the mobile nav toggle button
document.getElementById('nav-toggle').addEventListener('click', function() {
    const expandedCurrent = this.getAttribute('aria-expanded')
    
    // Sets classes and attributes on the nav-toggle
    this.classList.toggle('active')
    this.classList.toggle('closed')
    this.setAttribute('aria-expanded', expandedCurrent === 'true' ? 'false' : 'true')

    // Sets classes and attributes on the nav-toggle-menu
    menu = document.getElementById('nav-toggle-menu')
    menu.classList.toggle('active')
    menu.classList.toggle('closed')
})