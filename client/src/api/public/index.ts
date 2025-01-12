import axios from "axios";


const apiPublicClient = axios.create({
  baseURL: import.meta.env.VITE_BASE_URL,
});

apiPublicClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const { response } = error;

    if (response) {
      if (response.status === 401) {
        console.log("401 Ошибка авторизации");
      } else if (response.status === 400) {
        console.log("400 Bad Request");
      }
    } else {
      console.log("500 Ошибка сети");
    }
    return Promise.reject(error);
  }
);

export default apiPublicClient;
