rs.initiate(
    { 
        _id: "rs-config-server", 
        configsvr: true, 
        version: 1, 
        members: [
            { _id: 0, host: 'order_configserver01:27017' }, 
            { _id: 1, host: 'order_configserver02:27017' }, 
            { _id: 2, host: 'order_configserver03:27017' }
        ] 
    }
)