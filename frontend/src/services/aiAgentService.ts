import apiClient from "./api";

export interface AgentChatResponse {
  response: string;
}

export interface AgentChatBackgroundResponse {
  task_id: string;
  message: string;
}

export const aiAgentService = {
  /**
   * Chat with the AI agent for recommendations, model suggestion, and diagnostics.
   */
  chatWithAgent: async (
    message: string,
    background = false
  ): Promise<AgentChatResponse | AgentChatBackgroundResponse> => {
    const response = await apiClient.post<AgentChatResponse | AgentChatBackgroundResponse>(
      "/agent/chat",
      { message },
      {
        params: { background },
      }
    );
    return response.data;
  },
};
