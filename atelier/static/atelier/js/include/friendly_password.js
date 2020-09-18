$(document).ready(() => {
    $("[id^=show-password-widget-]").map((id, element) => {
        element.onclick = function() {
            let passwordInput = document.getElementById($(element).data()["selector"]);
            passwordInput.type = (passwordInput.type === "password") ? "text": "password"
        };
    });
});
