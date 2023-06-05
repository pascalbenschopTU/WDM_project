rs.initiate(
    { 
        _id: "order_rs-config-server", 
        configsvr: true, 
        version: 1, 
        members: [
            { _id: 0, host: "order-configserver01:28119" },
            // { _id: 1, host: "order-configserver02:28120" },
            // { _id: 2, host: "order-configserver03:28121" },
          ],
    }
)