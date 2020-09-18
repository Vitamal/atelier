document.addEventListener("DOMContentLoaded", function(event) {
    window.microsoft.login = new window.microsoft.objects.LoginController({
        'authorization_url': document.querySelector('#microsoft-login').dataset.url
    });
});
