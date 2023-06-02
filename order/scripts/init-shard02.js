rs.initiate(
    {
        _id: "rs-order_shard-02", 
        version: 1, 
        members: [ 
            { _id: 0, host: "order_shard02-a:27017" }, 
            { _id: 1, host: "order_shard02-b:27017" }, 
            { _id: 2, host: "order_shard02-c:27017" }
        ] 
    }
)