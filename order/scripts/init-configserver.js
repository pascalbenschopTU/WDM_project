rs.initiate(
    { 
        _id: "order_rs-config-server", 
        configsvr: true, 
        version: 1, 
        members: [
            { _id: 0, host: "order-configserver01:27116" },
            // { _id: 1, host: "order-configserver02:27117" },
            // { _id: 2, host: "order-configserver03:27118" },
          ],
    }
)