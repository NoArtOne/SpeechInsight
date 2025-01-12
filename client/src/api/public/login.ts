import apiPublicClient from "@/api/public/index";
import {isEmpty} from "lodash";

export const loginApi = (data: object) =>
    apiPublicClient.post('/auth/login', data);

export const companyInformationApi = (inn_or_ogrn: string, kpp: string, branch_type : enumCompanyBranch) => {
    const emptyOrKpp = isEmpty(kpp) ? '' : ` ${kpp}`;
    return apiPublicClient.get('/company-info/companies/suggest', { params: { q: `${inn_or_ogrn}${emptyOrKpp}`, branch_type } });
}

