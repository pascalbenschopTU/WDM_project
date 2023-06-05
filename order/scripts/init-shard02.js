rs.initiate(
    {
        _id: "order_rs-shard-02", 
        version: 1, 
        members: [ 
            { _id: 0, host: "order-shard02-a:27133" }, 
            { _id: 1, host: "order-shard02-b:27134" },
            { _id: 2, host: "order-shard02-b:27135" },
        ] 
    }
)