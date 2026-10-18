import {defineConfig} from 'vite'
export default defineConfig({optimizeDeps:{entries:['index.html','legacy.html']},server:{fs:{deny:['.git/**','research/**','assets/**','**/.env*']}}})
