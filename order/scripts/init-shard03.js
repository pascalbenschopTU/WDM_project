rs.initiate(
    {
        _id: "rs-order_shard-03", 
        version: 1, 
        members: [ 
            { _id: 0, host: "order-shard03-a:28128" },
            { _id: 1, host: "order-shard03-b:28129" },
            { _id: 2, host: "order-shard03-c:28130" },
        ] 
    }
)