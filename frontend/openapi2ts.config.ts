/** FastAPI 默认 OpenAPI JSON；请先启动后端再执行 npm run openapi2ts */
export default {
  requestLibPath: "import request from '@/request'",
  schemaPath: 'http://127.0.0.1:8567/openapi.json',
  serversPath: './src/services',
}
