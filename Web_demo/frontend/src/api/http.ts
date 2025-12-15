//\frontend\src\api\http.ts
import axios from "axios";
import type { AxiosError, InternalAxiosRequestConfig, AxiosResponse } from "axios";

const API_BASE_URL = "http://localhost:8000";
const REQUEST_TIMEOUT = 300000; // 5 minutes for long-running operations

/**
 * Configured axios instance with interceptors
 */
export const http = axios.create({
  baseURL: API_BASE_URL,
  timeout: REQUEST_TIMEOUT,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Request interceptor for logging and auth
 */
http.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Log request in development
    if (import.meta.env.DEV) {
      console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`);
    }

    // Add auth token if available
    // const token = localStorage.getItem('auth_token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }

    return config;
  },
  (error: AxiosError) => {
    console.error("[API Request Error]", error);
    return Promise.reject(error);
  }
);

/**
 * Response interceptor for error handling
 */
http.interceptors.response.use(
  (response: AxiosResponse) => {
    // Log response in development
    if (import.meta.env.DEV) {
      console.log(`[API Response] ${response.config.method?.toUpperCase()} ${response.config.url}`, response.status);
    }
    return response;
  },
  (error: AxiosError) => {
    // Enhanced error handling
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      const data = error.response.data as any;

      console.error(`[API Error ${status}]`, data?.detail || error.message);

      switch (status) {
        case 400:
          console.error("Bad Request:", data?.detail || "Invalid request");
          break;
        case 401:
          console.error("Unauthorized: Please login again");
          // Redirect to login if needed
          break;
        case 403:
          console.error("Forbidden: Access denied");
          break;
        case 404:
          console.error("Not Found:", error.config?.url);
          break;
        case 500:
          console.error("Server Error: Please try again later");
          break;
        case 503:
          console.error("Service Unavailable: Server is down");
          break;
        default:
          console.error("Error:", data?.detail || error.message);
      }
    } else if (error.request) {
      // Request made but no response
      console.error("[API Network Error] No response received:", error.message);
    } else {
      // Error in request setup
      console.error("[API Error]", error.message);
    }

    return Promise.reject(error);
  }
);

export default http;

