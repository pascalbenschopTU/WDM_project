# FROM rabbitmq:3.11.17-management
# RUN apt-get update && \
# apt-get install -y curl unzip

# RUN curl https://github.com/rabbitmq/rabbitmq-message-timestamp/releases/download/v3.11.2/rabbitmq_message_timestamp-v3.11.x.ez > rabbitmq_message_timestamp-v3.11.x.ez && \
# unzip rabbitmq_message_timestamp-v3.11.x.ez && \
# rm -f rabbitmq_message_timestamp-v3.11.x.ez && \
# mv rabbitmq_message_timestamp-v3.11.x.ez plugins/

# RUN rabbitmq-plugins enable rabbitmq_message_timestamp

FROM rabbitmq:3.11.17-management-alpine

RUN apk --no-cache add curl

RUN curl -L https://github.com/rabbitmq/rabbitmq-message-timestamp/releases/download/v3.11.2/rabbitmq_message_timestamp-v3.11.x.ez > rabbitmq_message_timestamp-v3.11.x.ez && \
mv rabbitmq_message_timestamp-v3.11.x.ez plugins/

RUN rabbitmq-plugins enable rabbitmq_message_timestamp