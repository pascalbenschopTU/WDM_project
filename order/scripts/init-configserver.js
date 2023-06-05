rs.initiate(
    { 
        _id: "order_rs-config-server", 
        configsvr: true, 
        version: 1, 
        members: [
            { _id: 0, host: "order-configsvr01:27116" },
            { _id: 1, host: "order-configsvr02:27117" },
            { _id: 2, host: "order-configsvr03:27118" },
          ],
    }
)