import { defineStore } from "pinia";
import { loginApi } from "@/api/public/login";
import { useUserStore } from "@/stores/userStore";


export type loginState = {
    email: string,
    password: string,
}

export const useLoginStore = defineStore('login',{
    state: () => ({
        email: null,
        password: null,
    } as loginState),
    getters: {
        getEmail: (state) => state.email,
        getPassword: (state) => state.password,
    },
    actions: {
        setEmail(email: string) { this.email = email; },
        setPassword(password: string) { this.password = password; },
        async login(success: Function, error: Function) {
            try {
                const response = await loginApi({ email: this.email, password: this.password });
                useUserStore().authorization(this.email, response.data.accessToken);
                success();
                this.password = null;
            } catch (err) {
                error();
                useUserStore().clearToken();
            }
        }
    }
})
