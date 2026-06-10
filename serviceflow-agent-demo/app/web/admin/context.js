import { sessionManager } from "../shared/session-manager.js";

export function adminContext() {
  const userId = sessionManager.getUserId() || "S1001";
  return {
    userId,
    role: sessionManager.getRole() || "agent",
    username: sessionManager.getUsername() || userId,
    agentId: userId,
  };
}

