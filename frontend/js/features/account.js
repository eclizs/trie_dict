import { getCurrentUser, logout } from "../core/api.js";
import { setHidden } from "../core/ui.js";

export async function initAccountControls() {
  const accountState = document.getElementById("account-state");
  const accountLabel = document.getElementById("account-label");
  const loginLink = document.getElementById("login-link");
  const registerLink = document.getElementById("register-link");
  const logoutButton = document.getElementById("logout-btn");

  if (!accountState || !accountLabel) return;

  const showGuest = () => {
    accountState.classList.remove("is-authenticated");
    accountLabel.textContent = "Guest session";
    setHidden(loginLink, false);
    setHidden(registerLink, false);
    setHidden(logoutButton, true);
  };

  const showUser = (user) => {
    accountState.classList.add("is-authenticated");
    accountLabel.textContent = user.email;
    setHidden(loginLink, true);
    setHidden(registerLink, true);
    setHidden(logoutButton, false);
  };

  try {
    showUser(await getCurrentUser());
  } catch {
    showGuest();
  }

  logoutButton?.addEventListener("click", async () => {
    logoutButton.disabled = true;
    accountLabel.textContent = "Logging out…";

    try {
      await logout();
      showGuest();
    } catch {
      accountLabel.textContent = "Could not log out";
    } finally {
      logoutButton.disabled = false;
    }
  });
}
