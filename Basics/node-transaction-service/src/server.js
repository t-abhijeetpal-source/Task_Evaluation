'use strict';

const createApp = require('./app');
const config = require('./config');
const logger = require('./logger');

const app = createApp();

app.listen(config.port, () => {
  logger.info('listening', { service: config.appName, port: config.port });
});
