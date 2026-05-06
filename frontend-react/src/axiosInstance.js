import axios from "axios";


const baseURL = import.meta.env.VITE_BACKEND_BASE_API
const axiosInstance = axios.create({
    baseURL: baseURL,
    headers: {
        'Content-Type': 'application/json',
        // This sets the default Content-Type header for all requests made with this axios instance to 'application/json', which is important for ensuring that the backend correctly interprets the data being sent in the request body as JSON. This way, we don't have to manually set the Content-Type header in every request we make with this instance; it will automatically include it for all requests.
    }
})


// Request Interceptor
axiosInstance.interceptors.request.use(
    function(config){
        const accessToken = localStorage.getItem('accessToken')
        if(accessToken){
            config.headers['Authorization'] = `Bearer ${accessToken}`
            // this adds the access token to the header of every request made using this axios instance, so we don't have to manually add it in every request in our components. It will automatically include the access token in the Authorization header for all requests made with this instance.
        }
        return config; 
        // returns means it will redirect back to the main section of the code and execute the request with the modified config (with the access token in the header)
    },
    function(error){
        return Promise.reject(error);
        // if there is an error in the request configuration, it will reject the promise and pass the error to the next handler (which could be a catch block in the component where the request was made)
    }
)

// Response Interceptor
axiosInstance.interceptors.response.use(
    function(response){
        return response;
        // if the response is successful (status code 2xx), it will simply return the response to the component where the request was made, allowing the component to handle the response data as needed.
    },
    // Handle failed responses
    async function(error){
        const originalRequest = error.config;
        if (error.response?.status === 401 && !originalRequest._retry && originalRequest.url !== '/token/refresh/') {
            originalRequest._retry = true;
            const refreshToken = localStorage.getItem('refreshToken');
            if (!refreshToken) {
                localStorage.removeItem('accessToken');
                localStorage.removeItem('refreshToken');
                window.location.href = '/login';
                return Promise.reject(error);
            }

            try {
                const response = await axiosInstance.post('/token/refresh/', { refresh: refreshToken });
                localStorage.setItem('accessToken', response.data.access);
                originalRequest.headers['Authorization'] = `Bearer ${response.data.access}`;
                return axiosInstance(originalRequest);
            } catch (refreshError) {
                localStorage.removeItem('accessToken');
                localStorage.removeItem('refreshToken');
                window.location.href = '/login';
                return Promise.reject(refreshError);
            }
        }
        return Promise.reject(error);
        // If the error is not a 401 or if the token refresh fails, it will reject the promise and pass the error to the next handler (which could be a catch block in the component where the request was made)
    }
)


export default axiosInstance;
// This file sets up a custom axios instance with a base URL and default headers, and it includes interceptors for handling authentication tokens. The request interceptor adds the access token to the headers of every request, while the response interceptor handles token refresh logic when a 401 Unauthorized response is received. This allows for seamless authentication handling across the application without needing to manually manage tokens in each component.